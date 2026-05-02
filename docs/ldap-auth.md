# LDAP/Active Directory Authentication with BIG-IP APM

## Overview

This document covers configuring LDAP/Active Directory authentication through BIG-IP APM. LDAP is the primary enterprise directory-backed credential validation mechanism for APM access policies.

## Architecture

```
Client → BIG-IP APM → LDAP/AD (bind + query) → Authorization → Backend App
```

## Prerequisites

- BIG-IP with APM licensed and provisioned
- Active Directory domain controller reachable from BIG-IP
- DNS resolution for AD domain and domain controllers
- Service account in AD for BIG-IP LDAP bind
- Network access to LDAP port 389 (or LDAPS 636)

## AD Auth Server Configuration

Create an AD Auth Server in APM:

```
Name:               ad-primary
Domain Name:        corp.example.com
Domain Controller:  10.0.1.10 (or DNS-resolvable DC hostname)
Bind DN:            svc-bigip@corp.example.com
Bind Password:      [encrypted credential]
Base DN:            DC=corp,DC=example,DC=com
```

In APM VPE, this is referenced by **AD Auth** and **AD Query** actions within an access policy.

## APM Access Policy Flow

### Standard LDAP Authentication

```
Start → Logon Page → AD Auth → AD Query (group lookup) → Allow/Deny
```

#### Step-by-Step VPE Configuration

1. **Start**: Entry point for the access policy
2. **Logon Page**: Collect username and password
   - Username field maps to `%{session.logon.last.username}`
   - Password field maps to `%{session.logon.last.password}`
3. **AD Auth Action**:
   - Auth Server: `ad-primary`
   - Username: `%{session.logon.last.username}`
   - Password: `%{session.logon.last.password}`
   - On Success → proceed to AD Query
   - On Failure → Access Deny
4. **AD Query Action**:
   - Retrieve user attributes (group membership, email, display name)
   - Set session variables for downstream authorization
5. **Branch/Allow/Deny**: Based on AD Query results (e.g., group membership)

### Multi-Domain LDAP Flow

For environments with multiple AD domains:

```
Start → Username Parse → Domain A suffix? → AD Auth A → Allow
                             ↓
                         Domain B suffix? → AD Auth B → Allow
```

Parse the `@domain` suffix from the username and route to the appropriate AD Auth Server.

## Session Variables

APM exposes these session variables after LDAP/AD operations:

| Variable | Source | Description |
|---|---|---|
| `session.logon.last.username` | Logon page | Submitted username |
| `session.ad.last.attr.memberOf` | AD Query | Group membership (semicolon-delimited) |
| `session.ad.last.attr.mail` | AD Query | Email address |
| `session.ad.last.attr.displayName` | AD Query | Full display name |
| `session.ad.last.attr.sAMAccountName` | AD Query | Windows logon name |
| `session.ad.last.attr.userPrincipalName` | AD Query | UPN (user@domain) |

## LDAP Best Practices

- Use a dedicated read-only service account for LDAP bind
- Configure multiple domain controllers for redundancy
- Prefer LDAPS (port 636) for encrypted LDAP traffic
- Set appropriate timeouts: 3-5 seconds for query, 10 seconds for bind
- Scope queries to specific OUs to improve performance in large directories
- Use nested group queries or specific group filters when needed

## LDAPS Certificate Trust

For encrypted LDAP connections, import the AD CA certificate:

```
System → Certificate Management → CA Certificate → Import
```

Then reference the CA bundle in the AD Auth Server configuration.

## LDAP Query Optimization

### OU-Scoped Queries

Restrict the search base to reduce latency:

```
Base DN: OU=Employees,DC=corp,DC=example,DC=com
```

### Group Filter Queries

Filter for specific group membership in the AD Query action:

```
Filter: (&(sAMAccountName=%{session.logon.last.username})(memberOf=CN=AppUsers,OU=Groups,DC=corp,DC=example,DC=com))
```

### Attribute Selection

Only retrieve needed attributes to reduce payload:

```
Attributes: memberOf,mail,displayName,sAMAccountName
```

## Troubleshooting

### Test LDAP Bind from BIG-IP CLI

```bash
ldapsearch -H ldap://10.0.1.10:389 \
  -D "svc-bigip@corp.example.com" \
  -W \
  -b "DC=corp,DC=example,DC=com" \
  "(sAMAccountName=testuser)"
```

### Common Errors

| Error | Cause | Fix |
|---|---|---|
| Bind timeout | DC unreachable or wrong port | Check DNS, network, firewall rules |
| Invalid credentials | Wrong bind DN or password | Verify service account credentials |
| No such object | Incorrect Base DN | Verify Base DN matches AD structure |
| Size limit exceeded | Query returns too many results | Scope to specific OU or add filter |
| LDAP_REFERRAL | DC forwards to another domain | Enable referral chasing or use global catalog |

### Enable APM Debug Logging

```bash
tmsh modify sys db log.apm.level value debug
tail -f /var/log/apm
```

Look for `AD Auth` and `AD Query` log entries to trace authentication flow.

## Git-Managed APM Policy

The repo manages APM through policy imports. To maintain LDAP-authenticated policies:

1. Export the access policy from BIG-IP VPE:
   ```
   Access Policy → Policies → Export → Download tar.gz
   ```
2. Place the exported file on the Ansible control host
3. Declare it in the APM policy import var tree:
   ```yaml
   # vars/security/apm/policies/access-policies.yml
   apm_policies:
     - name: ldap-auth-policy
       source: /opt/apm-policies/ldap-auth-policy.tar.gz
       type: access_policy
       reuse_objects: true
   ```

## Multiple Domain Support

For multi-forest or multi-domain environments:

1. Create separate AD Auth Servers per domain
2. Use APM policy branching based on username domain suffix
3. Configure cross-forest trust on the AD side
4. Route users to the correct domain controller based on their UPN suffix
