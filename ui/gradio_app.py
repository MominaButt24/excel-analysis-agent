import requests
import gradio as gr


API_URL = "http://127.0.0.1:8000"


def upload_file(file):
    if file is None:
        return "", "Please upload an XLSX file."

    try:
        with open(file, "rb") as f:
            response = requests.post(
                f"{API_URL}/upload",
                files={
                    "file": (
                        file.split("/")[-1],
                        f,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

        response.raise_for_status()

        data = response.json()

        return (
            data["file_id"],
            f"Uploaded successfully.\n\nSheets: {', '.join(data['sheets'])}",
        )

    except Exception as exc:
        return "", f"Upload failed: {exc}"


def ask_question(file_id, query):
    if not file_id:
        return "Please upload an XLSX file first."

    if not query.strip():
        return "Please enter a question."

    try:
        response = requests.post(
            f"{API_URL}/query",
            json={
                "file_id": file_id,
                "query": query,
            },
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "answer",
            str(data.get("result", "No result")),
        )

    except Exception as exc:
        return f"Query failed: {exc}"


with gr.Blocks(
    title="Excel Analysis Agent"
) as demo:

    gr.Markdown(
        """
        # 📊 Excel Analysis Agent

        Upload an Excel workbook and ask questions
        about its data.
        """
    )

    # file_id = gr.State("")
    file_id = gr.Textbox(
        label="File ID",
        interactive=False,
    )

    with gr.Row():

        with gr.Column():

            file = gr.File(
                label="Upload Excel Workbook",
                file_types=[".xlsx"],
                type="filepath",
            )

            upload_status = gr.Textbox(
                label="Upload Status",
                interactive=False,
                lines=2,
            )

        with gr.Column():

            query = gr.Textbox(
                label="Ask a Question",
                placeholder="e.g. What is the average unit cost?",
                lines=2,
            )

            analyze = gr.Button(
                "Analyze",
                variant="primary",
            )

    answer = gr.Markdown(
        label="Answer",
    )

    with gr.Accordion(
        "Analysis Details",
        open=False,
    ):

        details = gr.JSON(
            label="Details",
        )

    file.upload(
        upload_file,
        inputs=file,
        outputs=[file_id, upload_status],
    )

    def analyze_question(
        current_file_id,
        current_query,
    ):
        if not current_file_id:
            return "Please upload an XLSX file first.", {}

        if not current_query.strip():
            return "Please enter a question.", {}

        try:
            response = requests.post(
                f"{API_URL}/query",
                json={
                    "file_id": current_file_id,
                    "query": current_query,
                },
            )

            response.raise_for_status()

            data = response.json()

            return (
                data.get(
                    "answer",
                    str(data.get("result", "No result")),
                ),
                {
                    "sheet": data["plan"]["sheet"],
                    "operation": data["plan"]["operation"],
                    "column": data["plan"]["column"],
                    "filters": data["plan"]["filters"],
                    "result": data["result"],
                    "valid": data["valid"],
                },
            )

        except Exception as exc:
            return f"Query failed: {exc}", {}

    analyze.click(
        analyze_question,
        inputs=[file_id, query],
        outputs=[answer, details],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
    )