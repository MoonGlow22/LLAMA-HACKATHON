import nest_asyncio
import os
from llama_parse import LlamaParse

nest_asyncio.apply()
os.environ["LLAMA_CLOUD_API_KEY"] = "llx-6riLMbS7acdNBcqPwriJm4u809MImRgVGckbHJV3hlCMwzcE"
def test_llama_parse(link: str):
    
#%%
    documents_with_instruction = LlamaParse(
        result_type="markdown",
        system_prompt="This is a CV with Turkish characters."
    ).load_data(link)
    cv=""
    for i in range(len(documents_with_instruction)):
        cv+=documents_with_instruction[i].text+"\n"

    return cv

if __name__ == "__main__":
    link = "hazirCV.pdf"
    cv_text = test_llama_parse(link)
    print(cv_text)