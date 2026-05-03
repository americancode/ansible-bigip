PYTHON ?= python3
ANSIBLE_LOCAL_TEMP ?= .ansible/localtmp
ANSIBLE_REMOTE_TEMP ?= .ansible/tmp
VALIDATION_IMAGE ?= ansible-bigip-validation:latest

.PHONY: validate validate-vars validate-ansible validate-image-build validate-image-run

validate: validate-vars validate-ansible

validate-vars:
	$(PYTHON) tools/validate-vars.py

validate-ansible:
	mkdir -p $(ANSIBLE_LOCAL_TEMP) $(ANSIBLE_REMOTE_TEMP)
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ansible-playbook --syntax-check playbooks/ltm.yml
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ansible-playbook --syntax-check playbooks/gtm.yml
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ansible-playbook --syntax-check playbooks/ha.yml
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ansible-playbook --syntax-check playbooks/network.yml
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ansible-playbook --syntax-check playbooks/bootstrap.yml
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ansible-playbook --syntax-check playbooks/system.yml
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ansible-playbook --syntax-check playbooks/tls.yml
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ansible-playbook --syntax-check playbooks/security.yml

validate-image-build:
	docker build -f Dockerfile.validation -t $(VALIDATION_IMAGE) .

validate-image-run:
	docker run --rm -v "$$(pwd):/workspace" -w /workspace $(VALIDATION_IMAGE) make validate
