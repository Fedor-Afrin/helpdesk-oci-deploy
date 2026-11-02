terraform {
  required_providers {
    oci = {
      source = "oracle/oci"
    }

    helm = {
      source = "hashicorp/helm"
    }
  }

  backend "oci" {
    bucket    = "tfstate"
    namespace = "axm70tntbzcm"


  }

  # backend "local" {
  #   path = "errored.tfstate"
  # }

}

provider "oci" {
  region = var.region
}

# 1. Получаем список Availability Domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# 2. Скачиваем конфиг кластера
data "oci_containerengine_cluster_kube_config" "k8s_config" {
  cluster_id = oci_containerengine_cluster.k8s_cluster.id
}

# 4. Провайдер Helm
provider "helm" {
  kubernetes = {
    # БЕРЕМ ГОТОВЫЙ URL С HTTPS ИЗ КОНФИГА
    host = yamldecode(data.oci_containerengine_cluster_kube_config.k8s_config.content).clusters[0].cluster.server

    cluster_ca_certificate = base64decode(yamldecode(data.oci_containerengine_cluster_kube_config.k8s_config.content).clusters[0].cluster.certificate-authority-data)

    exec = {
      api_version = "client.authentication.k8s.io/v1beta1"
      args        = ["ce", "cluster", "generate-token", "--cluster-id", oci_containerengine_cluster.k8s_cluster.id, "--region", var.region]
      command     = "oci"
    }
  }
}
