#!/usr/bin/env bash
set -eu

trap 'kill_mlflow' EXIT

export AWS_ENDPOINT_URL="http://localhost:4566"
export AWS_REGION="us-west-2"

BUCKET_NAME="ml-models"
MLFLOW_LOGS="/tmp/mlflow_$$.out"
MLFLOW_PORT=5000
LOCALSTACK_PORT=4566

kill_mlflow() {
  kill $(ps ax | grep [m]lflow | awk '{print $1}')
}

echo "Run mlflow"
poetry run mlflow server --backend-store-uri 'sqlite:///mlruns/backend.db' --default-artifact-root 'artifacts' &>"${MLFLOW_LOGS}" &
echo "MLFlow is started as PID $!. The logs are in ${MLFLOW_LOGS}"

attempts=15
while ! curl -s -S localhost:${MLFLOW_PORT} 2>&1 | grep -q "You need to enable JavaScript to run this app"; do
  echo "Waiting for the MLFlow endpoint to be available"
  sleep 3
  (( attempts-- ))
  if [ "${attempts}" -eq 0 ]; then
    echo "MLFlow is not available after 30 secs. Check the logs:"
    cat "${MLFLOW_LOGS}"
    exit 1
  fi
done

docker-compose up --detach

while curl -s -S localhost:${LOCALSTACK_PORT} 2>&1 | grep -q "Couldn't connect to server"; do
  echo "Waiting for the Localstack endpoint to be available"
  sleep 1
done

echo "Create bucket if it wasn't created yet"
if aws s3 ls s3://${BUCKET_NAME} 2>&1 | grep -q NoSuchBucket; then
  echo "Create S3 bucket '${BUCKET_NAME}'"
  aws s3 mb s3://${BUCKET_NAME}
fi

echo "Train the model"
poetry run python diabetes_prediction_model.py data/diabetes_int_train.parquet "s3://${BUCKET_NAME}/model.pickle"

echo "Use the model and publish it to the registry"
poetry run python run_experiment.py data/diabetes_int_valid.parquet "s3://${BUCKET_NAME}/model.pickle"
