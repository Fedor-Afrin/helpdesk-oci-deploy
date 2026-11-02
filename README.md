# Helpdesk — Cloud-Native Deployment on Oracle Cloud Infrastructure

A cloud-native Helpdesk application deployed on **Oracle Cloud Infrastructure (OCI)** using **OKE, Terraform, Ansible, Helm, GitHub Actions, and Argo CD**.

This project demonstrates an end-to-end DevOps workflow: provisioning cloud infrastructure as code, configuring a Kubernetes environment, packaging application components with Docker, deploying them with Helm, and continuously reconciling application state through GitOps.

> **Project context:** DevOps graduation project developed as part of the training program at Spectrum Training and Testing Center.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Application Architecture](#application-architecture)
- [Cloud Infrastructure](#cloud-infrastructure)
- [Infrastructure Provisioning and Configuration](#infrastructure-provisioning-and-configuration)
- [CI/CD and GitOps Workflow](#cicd-and-gitops-workflow)
- [Repository Structure](#repository-structure)
- [Technology Stack](#technology-stack)
- [Configuration and Deployment](#configuration-and-deployment)
- [Security Considerations](#security-considerations)
- [Project Goals](#project-goals)

---

## Project Overview

The project is a web-based Helpdesk / Service Desk application running on Oracle Cloud Infrastructure.

It provides a workflow for creating and managing support tickets, assigning work to staff, tracking ticket status, and attaching reports or files to tickets.

The solution consists of containerized services deployed to **Oracle Kubernetes Engine (OKE)**. The infrastructure and platform components are automated rather than configured manually.

Main engineering goals:

- Provision cloud infrastructure using Terraform.
- Separate infrastructure provisioning from Kubernetes platform configuration.
- Use Ansible to orchestrate platform components and Helm-based deployments.
- Build and publish Docker images using GitHub Actions.
- Implement GitOps-based application delivery with Argo CD.
- Expose services through Traefik and an OCI-managed Load Balancer.
- Automate TLS certificate management and provide monitoring.

## Application Architecture

The application consists of three main runtime components:

| Component | Technology | Responsibility |
|---|---|---|
| Frontend | Python, Flask | Web interface, user sessions and interaction with the API |
| Backend | Python, FastAPI | REST API, authentication, user management and ticket processing |
| Database | PostgreSQL | Persistent storage for users, tickets and report metadata |

### Frontend

The Flask frontend provides the browser-facing interface. It handles login sessions and communicates with the backend through HTTP requests.

Features include:

- User authentication.
- Ticket dashboard.
- Ticket creation and details.
- Ticket status updates.
- Report comments and file attachments.
- Administrative user creation.

### Backend

The FastAPI backend exposes the application REST API. SQLAlchemy is used for database access and data models.

The main domain entities are:

- **Users** — regular users, staff members and administrators.
- **Tickets** — title, description, status, creator, assignee and timestamps.
- **Reports** — comments and references to files attached to tickets.

The API also provides a health endpoint at `/health`.

### File Storage

Ticket report files are uploaded to **OCI Object Storage** using its S3-compatible API.

PostgreSQL stores application data and report metadata, while uploaded objects are stored separately in cloud object storage.

### High-Level Application Flow

```text
             Users / Web Browser
                     |
                     v
              OCI Load Balancer
                     |
                     v
               Traefik Ingress
                     |
                     v
               Flask Frontend
                     |
                  HTTP API
                     |
                     v
               FastAPI Backend
                  /       \
                 v         v
            PostgreSQL  OCI Object Storage
              (data)     (report files)
```

---

## Cloud Infrastructure

The cloud environment is provisioned in **Oracle Cloud Infrastructure (OCI)**.

Terraform manages the foundational infrastructure:

- OCI Virtual Cloud Network (VCN).
- Internet Gateway.
- Route table and network routing.
- Security lists.
- Separate subnets for the Kubernetes API endpoint and worker nodes.
- Oracle Kubernetes Engine (OKE) cluster.
- OKE node pool.

The current Terraform configuration defines an OKE node pool with one worker node. It can be adapted to different capacity and availability requirements.

### Kubernetes Networking and Ingress

External application traffic is routed through **Traefik**, deployed as a Kubernetes Ingress Controller.

Traefik is installed by Terraform using the **Terraform Helm provider**. This is intentional: Traefik belongs to the infrastructure-facing networking layer.

Its Kubernetes `LoadBalancer` Service includes OCI-specific annotations. When the Service is created, OCI integration provisions an OCI Load Balancer and associates it with the configured node subnet and load-balancer settings.

The provisioning sequence is:

1. Terraform creates the VCN, subnets, security lists, OKE cluster and node pool.
2. Terraform connects to the newly created Kubernetes cluster through the Helm provider.
3. Terraform installs Traefik from its Helm chart.
4. The Traefik `LoadBalancer` Service and OCI annotations request an OCI Load Balancer.
5. Traefik routes incoming requests to Kubernetes Services according to Ingress resources.

This keeps the public entry point and ingress controller within the infrastructure provisioning stage.

## Infrastructure Provisioning and Configuration

The deployment is deliberately divided into two stages: **Terraform for infrastructure provisioning** and **Ansible for Kubernetes platform configuration**.

### Stage 1 — Terraform: Infrastructure as Code

Terraform provisions the OCI resources and prepares the Kubernetes environment.

Responsibilities include:

- Creating the OCI network foundation.
- Configuring subnets, routing and security lists.
- Creating the OKE cluster and worker node pool.
- Retrieving Kubernetes cluster connection information.
- Configuring the Terraform Helm provider to authenticate to OKE.
- Installing Traefik through its Helm chart.
- Triggering OCI Load Balancer provisioning through the Traefik Service annotations.

Terraform therefore establishes both the cloud infrastructure and the initial ingress infrastructure required by the platform.

### Stage 2 — Ansible: Kubernetes Platform Configuration

After the OKE cluster is available, Ansible configures the services running on top of Kubernetes.

The playbooks use the `kubernetes.core` collection, including its Helm module, to install and configure platform components.

| Component | Deployment method | Purpose |
|---|---|---|
| cert-manager | Helm | TLS certificate management |
| Let's Encrypt ClusterIssuer | Kubernetes resource | Production certificates using ACME HTTP-01 |
| Argo CD | Kubernetes manifests | GitOps continuous delivery |
| Prometheus and Grafana | Helm (`kube-prometheus-stack`) | Metrics collection and monitoring |
| Kubernetes Dashboard | Helm | Kubernetes web interface |
| Helpdesk Argo CD Application | Kubernetes custom resource | Registers the application repository and Helm chart |
| Application and Grafana Ingresses | Kubernetes resources | Publishes services through Traefik with TLS |

The Helpdesk application itself is deployed and continuously reconciled by Argo CD from the Helm chart stored in this repository.

### Why Terraform and Ansible Are Both Used

The tools have separate responsibilities:

- **Terraform** manages cloud infrastructure and infrastructure-dependent components, such as the ingress controller and OCI Load Balancer integration.
- **Ansible** configures the Kubernetes platform after the cluster exists, installing operational services and registering the application.
- **Helm** provides repeatable, parameterized Kubernetes deployments.
- **Argo CD** continuously reconciles the application deployment with the desired state stored in Git.

This separation makes the deployment process easier to understand, maintain and extend.

---

## CI/CD and GitOps Workflow

The project uses **GitHub Actions** for CI and image publishing, and **Argo CD** for GitOps-based deployment to Kubernetes.

The `main` and `test` branches have intentionally different responsibilities.

### Branch Strategy

| Branch | Docker image tags | Updates Helm `values.yaml` | Production GitOps update |
|---|---|---|---|
| `test` | `test-latest` | No | No |
| `main` | `latest` and commit SHA | Yes | Yes, through Argo CD |

### Test Branch

A push to `test` triggers the GitHub Actions workflow.

The workflow:

1. Checks out the repository.
2. Authenticates to Docker Hub using GitHub Actions secrets.
3. Builds the backend and frontend Docker images.
4. Pushes both images with the `test-latest` tag.

The test workflow does **not** update image tags in `charts/helpdesk-app/values.yaml`.

Therefore, it does not change the production image references monitored by the Argo CD application.

This allows the test branch to validate application builds without changing the production GitOps deployment state.

### Main Branch

A push to `main` triggers the production image workflow.

The workflow:

1. Checks out the repository.
2. Authenticates to Docker Hub.
3. Builds the backend and frontend Docker images.
4. Pushes each image with two tags:
   - `latest`
   - The Git commit SHA that triggered the workflow.
5. Updates backend and frontend image tags in `charts/helpdesk-app/values.yaml` to that commit SHA.
6. Commits and pushes the updated Helm values file back to `main`.

Using the commit SHA as the deployed image tag provides an explicit link between the application source revision and the container image version referenced by the Helm chart.

### Argo CD — GitOps Delivery

The Argo CD Application resource points to:

- **Repository:** `Fedor-Afrin/helpdesk-oci-deploy`
- **Branch:** `main`
- **Path:** `charts/helpdesk-app`
- **Values file:** `values.yaml`
- **Destination namespace:** `default`

Automated synchronization is enabled, including pruning and self-healing.

After GitHub Actions updates the image tags in `values.yaml`, Argo CD detects the Git change, renders the Helm chart and synchronizes the desired application state with the Kubernetes cluster.

### Complete Delivery Flow

```text
Developer pushes code
        |
        v
    GitHub branch
        |
        v
   GitHub Actions
        |
        +---------------------------+
        |                           |
        v                           v
  Build backend               Build frontend
        |                           |
        v                           v
  Push Docker image           Push Docker image
        |                           |
        +-------------+-------------+
                      |
           Branch-specific behavior
                      |
          +-----------+-----------+
          |                       |
          v                       v
      test branch             main branch
          |                       |
          v                       v
 Push test-latest tags    Push latest + SHA tags
          |                       |
          v                       v
 No Helm values update   Update Helm values.yaml
                                  |
                                  v
                         Commit change to main
                                  |
                                  v
                               Argo CD
                                  |
                                  v
                         Helm chart synchronization
                                  |
                                  v
                          Kubernetes deployment
```

This design separates image validation from production deployment and makes Git the source of truth for the application version running in Kubernetes.

---

## Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── main.yml
│
├── IaC(Terraform&Ansible/
│   ├── main.tf
│   ├── network.tf
│   ├── oke.tf
│   ├── helm_traefik.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── s3.tf
│   ├── terraform.tfvars.example
│   └── ansible/
│       ├── deploy_stack.yml
│       ├── argocd.yaml
│       ├── grafana.yaml
│       ├── helpdesk.yaml
│       └── k8s_dashboard.yaml
│
├── backend-app/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── crud.py
│   │   └── routers/
│   │       ├── auth.py
│   │       └── tickets.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend-app/
│   ├── templates/
│   ├── static/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── charts/
│   └── helpdesk-app/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│
└── argocd-app.yaml
```

## Technology Stack

| Area | Technologies |
|---|---|
| Cloud platform | Oracle Cloud Infrastructure |
| Managed Kubernetes | Oracle Kubernetes Engine (OKE) |
| Infrastructure as Code | Terraform, OCI provider |
| Kubernetes configuration | Ansible, `kubernetes.core` |
| Kubernetes packaging | Helm |
| Ingress and load balancing | Traefik, OCI Load Balancer |
| TLS certificates | cert-manager, Let's Encrypt |
| GitOps | Argo CD |
| CI/CD | GitHub Actions |
| Containerization | Docker |
| Container registry | Docker Hub |
| Frontend | Python, Flask |
| Backend | Python, FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Object storage | OCI Object Storage, S3-compatible API |
| Monitoring | Prometheus, Grafana |

---

## Configuration and Deployment

### Prerequisites

- OCI account with permissions to create networking resources, OKE clusters, node pools and Load Balancers.
- OCI CLI configured for the target account.
- Terraform with OCI and Helm providers.
- Ansible with the `kubernetes.core` collection.
- `kubectl` configured to access the OKE cluster.
- Helm.
- Docker and a Docker Hub account.
- GitHub repository with Actions enabled.
- DNS records for the configured application hostnames.

### Configuration

Do not commit real credentials or environment-specific secrets.

1. Copy `IaC(Terraform&Ansible/terraform.tfvars.example` to `terraform.tfvars`.
2. Populate the local file with OCI tenancy, user, compartment, region, API key path and SSH public key values.
3. Configure Docker Hub credentials as GitHub Actions secrets:
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`
4. Provide application and database credentials through Kubernetes Secrets.
5. Provide the Grafana administrator password through Ansible Vault or another secure secret-management mechanism.
6. Configure the domain name and certificate contact email.
7. Review Helm values and OCI-specific settings before applying the deployment.

The example Terraform variables file contains placeholders only. Keep the real `terraform.tfvars`, private keys, Terraform state files and secret values outside version control.

### Deployment Workflow

At a high level, the environment is deployed in this order:

1. Configure OCI credentials and Terraform variables locally.
2. Run Terraform to create the OCI network, OKE cluster, node pool and Traefik ingress infrastructure.
3. Configure `kubectl` access to the newly created OKE cluster.
4. Run the Ansible deployment playbook to install cert-manager, Argo CD, monitoring, Kubernetes Dashboard and the Helpdesk Argo CD Application.
5. Verify the OCI Load Balancer and DNS records for the configured hostnames.
6. Confirm that cert-manager has issued the required TLS certificates.
7. Push application changes to `test` to validate container builds.
8. Push approved changes to `main` to publish production image tags and update Helm values.
9. Verify that Argo CD detects and synchronizes the new desired state.

Environment-specific credentials, DNS records, secrets and OCI prerequisites must be supplied by the operator.

## Security Considerations

This repository is an engineering and learning project. Review the following items before using it for production workloads:

- Store credentials in a secure secret manager, Kubernetes Secrets or Ansible Vault; never commit secrets to Git.
- Rotate any credentials that may previously have been exposed.
- Restrict Kubernetes API, NodePort and Load Balancer access according to actual network requirements.
- Review Traefik API/dashboard exposure and disable insecure access modes.
- Review Kubernetes Dashboard authentication and RBAC. Avoid broad `cluster-admin` access for routine use.
- Use TLS for externally accessible services.
- Define resource requests, limits, persistent storage, backup and recovery policies.
- Review application authentication and authorization before exposing the service to untrusted users.

## Project Goals

This project demonstrates practical experience across several DevOps areas:

- Designing and provisioning cloud infrastructure with Terraform.
- Deploying and operating managed Kubernetes on OCI.
- Separating infrastructure provisioning from platform configuration.
- Using Terraform and Ansible Helm integrations for repeatable deployments.
- Building and publishing versioned container images through CI.
- Maintaining separate test and production delivery paths.
- Implementing GitOps with Argo CD and Helm.
- Integrating ingress, cloud load balancing, TLS automation and monitoring.
- Managing application data in PostgreSQL and file uploads in OCI Object Storage.

The central design principle is that infrastructure, platform configuration, container artifacts and application deployment are automated through distinct but connected stages. This keeps the deployment process reproducible and makes changes traceable from a Git commit to the image version running in Kubernetes.
