# Tiltfile mínima
allow_k8s_contexts('default')

custom_build(
    "transcriberapp-dev",
    "docker build -t transcriberapp-dev .",
    deps=['.'],
    live_update=[
        sync('.', '/app'),
        run('touch /app/reload.trigger'),
    ]
)

k8s_yaml("k3s/deployment-dev.yaml")

k8s_resource("transcriberapp", port_forwards=[9000])