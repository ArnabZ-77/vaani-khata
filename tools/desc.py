import os
from docx import Document
from docx.shared import Pt
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=Document(); st=d.styles['Normal']; st.font.name='Calibri'; st.font.size=Pt(11)
d.add_heading('Vaani Khata: voice ledger for small shops, powered by the Snapdragon NPU',1)
d.add_paragraph('Snapdragon® AI Lab Build & Present Challenge. Individual entry.')
d.add_heading('Problem',2)
d.add_paragraph("Small Indian shops record customer credit (udhaar) in paper khata books. Cloud ledger apps need internet, typing and accounts, and they upload sensitive who-owes-what data. Voice is the natural interface for a shopkeeper, but voice assistants normally send audio to the cloud.")
d.add_heading('Solution',2)
d.add_paragraph("Vaani Khata lets a shopkeeper speak entries in Hindi, English or Hinglish, for example \"Ramesh ne 500 rupaye udhaar liye\" or \"Sunita paid 200 rupees\". The speech is transcribed by Qualcomm AI Hub's Whisper-Small running on the Snapdragon Hexagon NPU. A parser turns the transcript into ledger entries (credit, payment, sale) stored in a local SQLite database. Balances update instantly, and the shopkeeper can ask \"How much does Ramesh owe?\". Hindi and English spellings of a name are merged into one customer. Everything runs on the laptop; nothing is sent to a server.")
d.add_heading('How Snapdragon is used',2)
for t in ["Whisper-Small encoder and decoder run as AI Hub precompiled QNN context binaries on the Hexagon NPU, via the ONNX Runtime QNN execution provider on Windows ARM64.",
          "Measured on a Snapdragon X (X126100) laptop: encoder for 30 s of audio takes about 115 ms on the NPU versus about 5.7 s on the CPU (about 50x). A 10.8 s spoken clip is transcribed end to end in about 0.65 s (about 16x real-time). On six Hindi and Hinglish test sentences (synthetic voices) all six produced correct ledger entries; the smaller Whisper-Base managed two of six, which is why Whisper-Small is the default.",
          "The app fails loudly if no NPU is found, so reported numbers are always NPU numbers."]:
    d.add_paragraph(t,style='List Bullet')
d.add_heading('Deployment and accessibility',2)
d.add_paragraph("Runs on any Snapdragon X Windows laptop with a single setup script that downloads the model from AI Hub. No cloud, no account, no recurring cost. Voice input removes the typing barrier and supports Hindi and English. The server binds to localhost, and data stays in one local file.")
d.add_heading('Limitations and next steps',2)
d.add_paragraph("Parsing is rule-based and may miss unusual phrasing; Hindi was tested with synthetic voices only, so accuracy in real noisy shops still needs field testing. Next: Llama 3.2 3B on the NPU for free-form understanding, and more Indian languages.")
d.add_heading('Links',2)
d.add_paragraph("Source code, setup steps and full benchmark data: see the GitHub repository submitted with this entry.")
d.save(os.path.join(R,'docs','VaaniKhata_Project_Description.docx'))
