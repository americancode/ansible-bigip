## gtm wide ip intent issues
- GTM doesn't follow the "intents" pattern of LTM for wide ips (for the vars,  playbooks seems to follow fine)

- If datacenter is defined as canonical object AND we are using the wide ip it has two objects in the data center objects       finalized array (likely should force usage of linked cannonical objects for datacenter and server OR make it clear and not cause duplicates)
  ok: [xxx] => (item=Common/lab-dc1)
  ok: [xxx] => (item=Common/lab-dc1)

- Autolookup from the wideip gtm "virtual-server" works but how to get the fully hydrated virtual server name
  if coming from the ltm cluster intent (which doesnt spell out the virtual server name)

- Validation issues with GTM wide ips. (loosen it up a bit)
     	python3 tools/validate-vars.py
	ERROR: vars/ltm/intents/clusters/dc1-rsc-xx-1/cluster-spec.yml: RKE2 server intent `dc1-rsc-xx-1` must define exactly two `worker_services` entries (fixed)
	Validation failed with 2 error(s).

- align gtm playbook with build vs compile language

Improvements:
  - Validation should probably check and ensure are never deleting and re-creating objects in the same pass? (maybe we already have this)
  - What are the compatibility flags for?
  - Ordering of servers in LTM/GTM pools

