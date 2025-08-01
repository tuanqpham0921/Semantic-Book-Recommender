import gradio as gr
import sys
from app.query_books import recommend_books
from app.create_chroma_db_books import create_chroma_db


categories = ['All', "Children's Fiction", "Children's Nonfiction", 'Fiction', 'Nonfiction']
tones = ["All"] + ["Happy", "Surprising", "Angry", "Suspenseful", "Sad"]

with gr.Blocks(theme = gr.themes.Glass()) as dashboard:
    gr.Markdown("# Semantic book recommender")

    with gr.Row():
        user_query = gr.Textbox(label = "Please enter a description of a book:",
                                placeholder = "e.g., A story about forgiveness")
        category_dropdown = gr.Dropdown(choices = categories, label = "Select a category:", value = "All")
        tone_dropdown = gr.Dropdown(choices = tones, label = "Select an emotional tone:", value = "All")
        submit_button = gr.Button("Find recommendations")

    gr.Markdown("## Recommendations")
    output = gr.Gallery(label = "Recommended books", columns = 8, rows = 2)

    submit_button.click(fn = recommend_books,
                        inputs = [user_query, category_dropdown, tone_dropdown],
                        outputs = output)


if __name__ == "__main__":
    if "--init-chroma" in sys.argv:
        create_chroma_db()
    else:
        # default it will be on localhost (127.0.0.1)
        # therefore onlt the local machine can access it
        # server_name listen to all network interfaces, and the port is set to 7860
        dashboard.launch(server_name="0.0.0.0", server_port=7860)