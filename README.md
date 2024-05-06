# eDU Workload Emulator Variant

A synthetic workload generator intended to emulate a RAN vDU/vCU implementation on OpenShift.

## Usage

The `automation` directory holds pieces of automation that will automate parts of deploying the eDU. Please see [automation/README.md](automation/README.md) for more information on usage.

# Directory Structure
```
├── automation
│   ├── README.md
│   ├── ansible.cfg
│   ├── playbooks
│   │   ├── create_partitions.yml #Create logical volumes
│   │   ├── setup_edu.yml #Setup workload on the SNO
│   │   └── teardown_edu.yml #Destroy workload from the SNO
│   └── roles
│       ├── setup_edu
│       ├── setup_lvs
│       └── teardown_edu
└── tools
    ├── configs.yaml #stress-ng configs
    ├── template.py
    ├── create_edu.py #python script to generate [fedora-stress-ng](https://github.com/abraham2512/fedora-stress-ng) based Kustomize overlays
    ├── pv.yaml
    ├── pvc.yaml
    ├── secrets
    ├── templates #Root Kustomization folder for overlays
    │   ├── base
    │   │   └── footprint
    │   │       ├── kustomization.yaml
    │   │       └── test1-deployment.yaml
    │   ├── kustomization.yaml
    │   └── overlays
    │       └── stressCPU
    │           ├── kustomization.yaml
    │           └── patch.yaml
    └── test-ns.yaml
```
