PYTHON ?= python3
ANSIBLE_LOCAL_TEMP ?= .ansible/localtmp
ANSIBLE_REMOTE_TEMP ?= .ansible/tmp

.PHONY: validate validate-vars validate-ansible

validate: validate-vars validate-ansible

validate-vars:
	$(PYTHON) tools/validate-vars

validate-ansible:
	mkdir -p $(ANSIBLE_LOCAL_TEMP) $(ANSIBLE_REMOTE_TEMP)
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ansible-playbook --syntax-check ltm.yml
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ansible-playbook --syntax-check gtm.yml
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ansible-playbook --syntax-check network.yml
