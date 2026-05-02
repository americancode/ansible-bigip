# Kerberos SSO with BIG-IP APM

## Overview

This document covers configuring Kerberos-based Single Sign-On (SSO) through BIG-IP APM. Kerberos SSO enables seamless authentication for domain-joined clients and Kerberos Constrained Delegation (KCD) for transparent backend application access.

## Architecture

```
Client (SPNEGO) → BIG-IP APM → AD/KDC (TGT) → KCD → Backend App (Kerberos ticket)
```

Two Kerberos use cases in APM:
1. **SPNEGO authentication** — client proves identity to APM via Kerberos
2. **KCD SSO** — APM obtains a Kerberos ticket on behalf of the user for backend apps

## Prerequisites

- BIG-IP with APM licensed and provisioned
- Active Directory domain controller reachable from BIG-IP
- DNS resolution for AD domain and domain controllers
- NTP configured on BIG-IP (Kerberos is time-sensitive; max 5 min skew)
- Service account in AD for KCD
- SPN registration for backend services

## Keytab Generation

Generate a keytab file on the Active Directory domain controller:

```powershell
# On AD Domain Controller (PowerShell)
ktpass -princ HTTP/bigip.corp.example.com@CORP.EXAMPLE.COM `
       -mapuser svc-bigip-kerb@corp.example.com `
       -pass * `
       -crypto AES256-SHA1 `
       -ptype KRB5_NT_PRINCIPAL `
       -out C:\temp\bigip.keytab
```

Upload the keytab to BIG-IP:

```
System → File Management → Kerberos Keytab → Import
```

## Kerberos SSO Object Configuration

Create a Kerberos SSO object in APM for KCD:

```
Name:               kcd-backend-app
Keytab:             /config/filestore/files_d/Common_d/keytab_d/bigip.keytab
Service Principal:  HTTP/app-backend.corp.example.com@CORP.EXAMPLE.COM
KDC:                10.0.1.10 (or DNS-resolvable DC)
Realm:              CORP.EXAMPLE.COM
```

## SPN Registration

Register the SPN for the backend service on the AD domain controller:

```powershell
setspn -S HTTP/app-backend.corp.example.com svc-backend-app
```

The service account (`svc-backend-app`) must be trusted for delegation to the BIG-IP service account.

## SPNEGO Authentication

SPNEGO provides seamless SSO for domain-joined browsers. Configure in VPE:

1. Add an **SPNEGO Auth** action at the start of the access policy
2. Configure the fallback flow to a logon page for non-domain devices:

```
Start → SPNEGO Auth → Success? → KCD SSO → Allow
                    ↓ (fail)
                Logon Page → AD Auth → KCD SSO → Allow
```

SPNEGO requires:
- Client browser configured for Integrated Windows Authentication
- BIG-IP hostname accessible via the AD domain (e.g., `bigip.corp.example.com`)
- SPN `HTTP/bigip.corp.example.com` registered on the BIG-IP service account

## KCD SSO in Access Policies

After authenticating the user (via SPNEGO or form-based AD Auth), add a KCD SSO action:

```
KCD SSO Action Configuration:
  Kerberos SSO Object:  kcd-backend-app
  Username Source:      %{session.logon.last.username}
  UPN Suffix:           @corp.example.com
```

The KCD action obtains a service ticket for the backend application on behalf of the authenticated user and injects it into the HTTP request (Authorization: Negotiate header).

## Session Variables

APM exposes these session variables for Kerberos flows:

| Variable | Source | Description |
|---|---|---|
| `session.logon.last.username` | SPNEGO / Logon page | User identity |
| `session.spnego.last.username` | SPNEGO Auth | SPNEGO-resolved username |
| `session.kcd.username` | KCD SSO | Kerberos principal name |
| `session.kcd.ticket` | KCD SSO | Base64-encoded service ticket |

## Troubleshooting

### Time Sync

Kerberos fails if clock skew exceeds 5 minutes. Verify NTP:

```bash
tmsh show sys ntp
```

### KDC Reachability

Test KDC connectivity from BIG-IP:

```bash
ping -c 3 10.0.1.10
tcpdump -i mgmt -nn port 88
```

### Keytab Validation

Verify keytab contents:

```bash
klist -kt /config/filestore/files_d/Common_d/keytab_d/bigip.keytab
```

Expected output shows the service principal and key version number (kvno).

### Common Errors

| Error | Cause | Fix |
|---|---|---|
| `KRB5KDC_ERR_C_PRINCIPAL_UNKNOWN` | SPN not registered | Run `setspn` on DC |
| `KRB5KDC_ERR_PREAUTH_FAILED` | Wrong keytab or password | Regenerate keytab with correct password |
| `KRB5KRB_AP_ERR_SKEW` | Clock skew > 5 min | Sync NTP on BIG-IP |
| `KRB5KDC_ERR_S_PRINCIPAL_UNKNOWN` | Backend SPN missing | Register backend SPN with `setspn` |
| `KRB5KDC_ERR_POLICY` | Account restrictions | Check AD account flags (password expiry, logon hours) |
| SPNEGO fails, form works | Browser not in trusted zone | Add BIG-IP URL to IE/Edge Local Intranet zone |

### Enable APM Debug Logging

```bash
tmsh modify sys db log.apm.level value debug
tail -f /var/log/apm
```

Look for `Kerberos`, `SPNEGO`, and `KCD` log entries.

## Multi-Realm Support

For cross-forest or multi-realm environments:

1. Create separate Kerberos SSO objects per realm
2. Use separate keytabs for each realm
3. Configure realm trust on the AD side
4. Route users to the correct KCD object based on their UPN realm

```
Start → SPNEGO/AD Auth → Realm A? → KCD A → Allow
                         ↓
                     Realm B? → KCD B → Allow
```

## Git-Managed Kerberos Flows

This repo keeps APM tmsh-driven. For Kerberos-authenticated access flows:

1. Declare the Kerberos object in `vars/security/apm/sso_configs/`
2. Declare any AD or LDAP auth server objects in `vars/security/apm/auth_servers/`
3. Build the access-policy flow with `vars/security/apm/policy_nodes/`
4. Attach the resulting access policy and any per-session policy through `vars/security/apm/access_profiles/`

That keeps the entire Kerberos flow reviewable as YAML object definitions instead of opaque exported `tar.gz` policy bundles.
