- GTM doesn't follow the "intents" pattern of LTM for wide ips (for the vars,  playbooks seems to follow fine)
- Port in big ip credential (the custom credential)
- Bad inline jinja comments (no inline stuff)
- Validation issues with GTM wide ips. (loosen it up a bit)
     	python3 tools/validate-vars.py
	ERROR: vars/ltm/intents/clusters/dc1-rsc-xx-1/cluster-spec.yml: RKE2 server intent `dc1-rsc-xx-1` must define exactly two `worker_services` entries
	Validation failed with 2 error(s).

- 'Compatibility' not a field of GTM tcp https monitor
- If datacenter is defined as canonical object AND we are using the wide ip it has two objects in the data center objects       finalized array
  ok: [xxx] => (item=Common/lab-dc1)
  ok: [xxx] => (item=Common/lab-dc1)
- Autolookup from the wideip gtm "virtual-server" works but how to get the fully hydrated virtual server name
  if coming from the ltm cluster intent (which doesnt spell out the virtual server name)
- align gtm playbook with build vs compile language

Improvements:
  - Validation should probably check and ensure are never deleting and re-creating objects in the same pass
  - What are the compatibility flags for?

