import openai
import json
import fitz  # PyMuPDF for PDF handling
import docx  # python-docx for DOCX files
import requests

# Ensure you have a valid OpenAI API key set
openai.api_key = 'YOUR_API_KEY'

def extract_text_from_pdf(pdf_path):
    try:
        pdf_document = fitz.open(pdf_path)
        full_text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            full_text += page.get_text()
        return full_text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(docx_path):
    try:
        doc = docx.Document(docx_path)
        full_text = [paragraph.text for paragraph in doc.paragraphs]
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""

def fetch_text_from_url(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching text from URL: {e}")
        return ""

def split_text_into_chunks(text, chunk_size=1500):
    chunks = []
    while len(text) > chunk_size:
        chunk = text[:chunk_size]
        last_space = chunk.rfind(" ")
        if last_space == -1:
            last_space = chunk_size
        chunks.append(text[:last_space].strip())
        text = text[last_space:].strip()
    if text:
        chunks.append(text)
    return chunks

def generate_questions_and_answers(text, num_questions=5):
    if not text.strip():
        print("The input text is empty. Please check the text content.")
        return {"qa_pairs": []}
    
    prompt = f"Given the following text, generate {num_questions} questions and their corresponding answers:\n\n{text}"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150 * num_questions,
            temperature=0.7
        )
        
        print("Raw Response:")
        print(json.dumps(response, indent=2))  # Debugging output
        
        qa_pairs = []
        q_and_a_text = response['choices'][0]['message']['content'].strip()
        if not q_and_a_text:
            print("No questions and answers were generated.")
            return {"qa_pairs": []}
        
        lines = q_and_a_text.split("\n")
        question = None
        answer = None

        for line in lines:
            line = line.strip()
            if line.startswith(("1.", "2.", "3.", "4.", "5.")):
                if question and answer:
                    qa_pairs.append({"question": question, "answer": answer})
                question = line
                answer = ""
            elif line.startswith("-"):
                answer = line[1:].strip()

        if question and answer:
            qa_pairs.append({"question": question, "answer": answer})
        
        return {"qa_pairs": qa_pairs}
    
    except Exception as e:
        print(f"Error during API call: {e}")
        return {"qa_pairs": []}

def main(input_source, num_questions=5, chunk_size=1500):
    if input_source.lower().endswith('.pdf'):
        text = extract_text_from_pdf(input_source)
    elif input_source.lower().endswith('.docx'):
        text = extract_text_from_docx(input_source)
    elif input_source.startswith('http://') or input_source.startswith('https://'):
        text = fetch_text_from_url(input_source)
    else:
        print("Unsupported input source. Please provide a PDF, DOCX, or a URL.")
        return
    
    if not text:
        print("No text extracted. Please check your input source.")
        return
    
    text_chunks = split_text_into_chunks(text, chunk_size)
    all_qa_pairs = {"qa_pairs": []}
    
    for chunk_num, chunk_text in enumerate(text_chunks):
        print(f"Generating Q&A for Chunk {chunk_num + 1}...")
        qa_pairs = generate_questions_and_answers(chunk_text, num_questions)
        all_qa_pairs["qa_pairs"].extend(qa_pairs["qa_pairs"])

    print("Final Q&A Pairs:")
    print(json.dumps(all_qa_pairs, indent=2))  # Debugging output
    
    with open('qa_pairs.json', 'w') as json_file:
        json.dump(all_qa_pairs, json_file, indent=2)

# Example usage
input_path_or_url = r'path\to\your\file.pdf'  # Replace with your file path or URL
main(input_path_or_url, num_questions=5)
