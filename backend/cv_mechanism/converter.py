from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from cv_mechanism.main_converter import test_llama_parse
import re
import re

import re

from typing import Dict, List

import re

def raporu_ayir(rapor_metni):
    # Başlıkları bul (**: ile biten veya ** ile sarılmış olanlar)
    basliklar = re.findall(r'\*\*(.*?)\*\*:?', rapor_metni)
    
    bolumler = {}
    
    for i, baslik in enumerate(basliklar):
        baslik = baslik.strip()
        # Mevcut başlığın konumunu bul
        baslik_pattern = re.escape(f"**{baslik}**")
        start = re.search(baslik_pattern, rapor_metni)
        
        if start:
            start_pos = start.end()
            # Bir sonraki başlığın başlangıcını bul
            next_start = len(rapor_metni)
            if i + 1 < len(basliklar):
                next_baslik_pattern = re.escape(f"**{basliklar[i+1]}**")
                next_match = re.search(next_baslik_pattern, rapor_metni[start_pos:])
                if next_match:
                    next_start = start_pos + next_match.start()
            
            # Bu başlığın içeriğini al
            icerik = rapor_metni[start_pos:next_start].strip()
            
            # Tüm satırları temizle ve yeni satırlarla birleştir
            satirlar = icerik.split('\n')
            temiz_satirlar = []
            
            for satir in satirlar:
                satir = satir.strip()
                if satir and not satir.startswith('**'):
                    temiz_satir = re.sub(r'^(\d+\.|•|\-)\s*', '', satir)
                    temiz_satirlar.append(temiz_satir)
            
            # Tüm maddeleri yeni satır karakterleri ile birleştir
            tek_string_icerik = '\n'.join(temiz_satirlar)
            bolumler[baslik] = tek_string_icerik
    
    return bolumler



def extract_report(text: str) -> str:
    """
    Model çıktısından 'Report:' kelimesinden sonrasını çeker.
    Eğer böyle bir ifade yoksa orijinal metni döner.
    """
    match = re.search(r"Report:\s*(.*)", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()

model_name = "Geetansh007/Counsellor"
print("Model yükleniyor...")

# Cihaz seçimi (GPU varsa kullan)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Kullanılan cihaz:", device)

# Model + Tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

def full_stream(link):
    cv_text = test_llama_parse(link).strip()

    prompt = f"""
You are an expert career counsellor and CV analyst.

Carefully analyze the CV and provide a detailed, structured report with the sections below:

1. Short Summary
2. Key Strengths
3. Weaknesses / Gaps
4. Suggested Job Roles
5. Improvement Suggestions
6. ATS Keywords
7. Interview Preparation Tips
8. Potential Interview Questions
9. CV Score (out of 100)

CV to analyze:
{cv_text}

Write the output in a clean format. Start with: "Report:"
"""

    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            max_new_tokens=900,
            do_sample=True,
            temperature=0.7,
            top_p=0.9
        )

    output_text = tokenizer.decode(output_tokens[0], skip_special_tokens=True)
    report = extract_report(output_text)
    print(report)
    return raporu_ayir(report)

if __name__ == "__main__":
    link = "backend/hazirCV.pdf"
    result = full_stream(link)
    print("\nAnaliz tamamlandı. İşte rapor:\n")
    for section, items in raporu_ayir(result).items():
        print(f"== {section} ==")
        
        print(f"- {items}")
        
