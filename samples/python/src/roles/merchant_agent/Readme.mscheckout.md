# Readme JPMC Checkout AP2 demo


### For setting up grpc-web.

```
pip3 install grpcio-tools googleapis-common-protos
```

merge all proto into one, for Pay() grpc-web call:

```
python3 -m grpc_tools.protoc --proto_path=proto_exp --proto_path=/Users/I793486/Library/Python/3.12/lib/python/site-packages  --python_out=generated --grpc_python_out=generated proto_exp/checkout/fe/v1/*.proto
```

