# helm_traefik.tf


resource "helm_release" "traefik" {
  name             = "traefik"
  repository       = "https://traefik.github.io/charts"
  chart            = "traefik"
  namespace        = "traefik"
  create_namespace = true

  wait            = true
  timeout         = 600
  cleanup_on_fail = true

  values = [
    yamlencode({
      # 1. Настройки балансировщика Oracle (OCI)
      service = {
        annotations = {
          "service.beta.kubernetes.io/oci-load-balancer-shape"          = "flexible"
          "service.beta.kubernetes.io/oci-load-balancer-shape-flex-min" = "10"
          "service.beta.kubernetes.io/oci-load-balancer-shape-flex-max" = "100"

          # АВТОМАТИЗАЦИЯ: Берем ID подсети динамически
          "service.beta.kubernetes.io/oci-load-balancer-subnet1" = oci_core_subnet.oke_nodes_subnet.id

          # АВТОМАТИЗАЦИЯ БЕЗОПАСНОСТИ:
          "service.beta.kubernetes.io/oci-load-balancer-security-list-management-mode" = "All"
        }
      }

      # 2. Аргументы для API и логов
      additionalArguments = [
        "--api.insecure=true",
        "--accesslog=true"
      ]
    })
  ]
  depends_on = [oci_containerengine_node_pool.k8s_node_pool]
}
