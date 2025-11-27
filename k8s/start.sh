kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f database.yaml
read -t 15 -p "Wait till the databases get up and running..."
echo
kubectl apply -f stocks_server.yaml
read -t 15 -p "Wait till the server get up and running..."
echo
kubectl apply -f stocks_client.yaml
kubectl apply -f stocks_node_gen.yaml
