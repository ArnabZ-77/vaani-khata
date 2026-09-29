import onnxruntime as ort, onnxruntime_qnn as q, time, sys, glob, numpy as np
ort.register_execution_provider_library(q.get_ep_name(), q.get_library_path())
npu=[d for d in ort.get_ep_devices() if d.ep_name=='QNNExecutionProvider' and 'NPU' in str(d.device.type)]
so=ort.SessionOptions(); so.add_provider_for_devices(npu,{})
d=glob.glob(r'D:\Desktop\snapdragon\models\whisper_base\*')[0]
t=time.time(); s=ort.InferenceSession(d+r'\encoder.onnx',sess_options=so); print('load',time.time()-t)
print(s.get_providers(),[ (i.name,i.shape,i.type) for i in s.get_inputs()])
x=np.random.randn(1,80,3000).astype(np.float16)
for i in range(4):
    t=time.time(); o=s.run(None,{'input_features':x}); print('enc',time.time()-t)
