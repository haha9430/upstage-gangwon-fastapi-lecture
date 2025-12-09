# K8s 배포 가이드

## 배포 방법
Docker image `upstage-gangwon-backend:lite`

```bash
# 모든 리소스 배포
kubectl apply -f .

# 상태 확인
kubectl get all -n gangwon
```

## 접근 방법

NodePort로 접근:
```bash
# minikube 사용 시
minikube service backend-nodeport -n gangwon

# 직접 접근 (노드 IP 필요)
curl http://<node-ip>:30880/agent/health
```

## 테스트

```bash
curl -X POST http://<node-ip>:30880/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "테스트"}'
```

## 로그 확인
   ```bash
   # Check all resources
   kubectl get all -n upstage-gangwon

   # Check pod logs
   kubectl logs -f deployment/upstage-gangwon-backend -n upstage-gangwon
   kubectl logs -f deployment/chromadb -n upstage-gangwon
   ```

## 사전 설정

- **UPSTAGE_API_KEY**: Update the base64 encoded value in `02-configmap.yaml`
- **Domain**: Change `upstage-gangwon.local` in `05-ingress.yaml` to your actual domain
- **Resources**: Adjust CPU/memory requests and limits in deployment manifests


## 정리

```bash
kubectl delete namespace gangwon
```