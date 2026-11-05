import uvicorn


def main():
    print("==================================================")
    print("🚀 Starting Agentic CRM Assistant Chatbot UI")
    print("📡 Server: http://localhost:8000")
    print("💬 Open http://localhost:8000 in your browser")
    print("==================================================")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
