kubectl delete -f stocks_client.yaml
timeout 15
kubectl delete -f stocks_server.yaml
timeout 15
kubectl delete -f database.yaml
timeout 60
kubectl delete -f secret.yaml
kubectl delete -f configmap.yaml
timeout 15
kubectl delete -f namespace.yaml




