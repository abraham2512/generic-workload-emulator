# Automation

The automation directory contains Ansible tooling to automate deployment of the eDU. The playbooks are simple wrappers around the roles, use whichever is more appropriate for your use case.

## Inventory

See one of the inventory files in `automation` to see how to set up your inventory. 

Note that the Ansible controller will need to be able to SSH to the node for the partition creation.

## Partitions

The eDU requires 26x10 Gi partitions on the host machine, as specified in the [setup_lvs role](automation/roles/setup_lvs/defaults/main.yml`). These are not being created using a `MachineConfig` in order to avoid a cluster restart. Note that these partitions will persist across redeploys of the cluster so it is only needed once per node.

Create partitions on the target cluster using the `create_partitions` playbook:

```shell
ansible-playbook playbooks/create_partitions.yml -i 303_sno2.yml
```

This will SSH into the machine and create the required LVs

## eDU deployment

To setup the eDU use the `setup_edu` playbook (or role).

```shell
ansible-playbook playbooks/setup_edu.yml -i 303_sno2.yml
```

There is the option to include or remove the requirement for some pods to have SR-IOV networking available by setting the `enable_sriov` variable. By default SR-IOV is not required. For example, to require SR-IOV on some pods, use:

```shell
ansible-playbook playbooks/setup_edu.yml -i 303_sno2.yml
```

## eDU Teardown

To remove the eDU from a cluster, use the `teardown_edu` playbook (or role).

```shell
ansible-playbook playbooks/teardown_edu.yml -i 303_sno2.yml
```

There is the option to remove only the pods, leaving the namespace and persistent volumes in place for testing purposes, using the `remove_pods_only` variable. By default the entire namespace will be removed, including the persistent volumes. For example, to leave the PVs:

```yaml
    - include_role:
        name: teardown_edu
      vars:
          kubeconfig_file: "{{ hostvars['cluster'].kubeconfig_file }}"
          remove_pods_only: true
```
