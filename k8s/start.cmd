kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f database.yaml
timeout 15
kubectl apply -f stocks_server.yaml
timeout 15
kubectl apply -f stocks_client.yaml
