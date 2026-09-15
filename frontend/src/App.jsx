import { useEffect, useRef, useState } from "react";

function renderMessage(text) {
  const urlRegex = /(https?:\/\/[^\s\])]+)/g;

  const parts = text.split(urlRegex);

  return parts.map((part, index) => {
    if (part.match(/^https?:\/\//)) {
      return (
        <a
          key={index}
          href={part}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-500 hover:underline break-all"
        >
          {part}
        </a>
      );
    }

    return <span key={index}>{part}</span>;
  });
}

function App() {
  const [darkMode, setDarkMode] = useState(false);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const [activeTool, setActiveTool] = useState(null);

  const messagesEndRef = useRef(null);

  const suggestions = [
    "Tell me about Aryan",
    "What are the main skills?",
    "Explain the main projects",
    "What experience does Aryan have?",
    "What is Aryan's education?",
    "Why should we hire Aryan?",
  ];

  const tools = [
    {
      id: "resume",
      label: "View resume",
      icon: "↑",
    },
  ];

  // =====================================================
  // AUTO SCROLL
  // =====================================================

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  // =====================================================
  // SEND MESSAGE
  // =====================================================

  const sendQuestion = async (text = question) => {
    const currentQuestion = text.trim();

    if (!currentQuestion || loading) return;

    const userMessage = {
      role: "user",
      content: currentQuestion,
    };

    const updatedMessages = [...messages, userMessage];

    // Add user message immediately
    setMessages(updatedMessages);

    // Clear input immediately
    setQuestion("");

    setLoading(true);

    try {
      const API_URL = import.meta.env.VITE_API_URL;

      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: updatedMessages,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();

        console.error("STATUS:", response.status);
        console.error("BACKEND RESPONSE:", errorData);

        throw new Error(JSON.stringify(errorData));
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let aiContent = "";

      // Create empty AI message
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "",
        },
      ]);

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value, {
          stream: true,
        });

        aiContent += chunk;

        setMessages((prev) => {
          const updated = [...prev];

          updated[updated.length - 1] = {
            role: "assistant",
            content: aiContent,
          };

          return updated;
        });
      }

      // Flush any remaining decoder content
      const finalChunk = decoder.decode();

      if (finalChunk) {
        aiContent += finalChunk;

        setMessages((prev) => {
          const updated = [...prev];

          updated[updated.length - 1] = {
            role: "assistant",
            content: aiContent,
          };

          return updated;
        });
      }
    } catch (error) {
      console.error("AI Error:", error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            error.message || "Sorry, I couldn't connect to the AI assistant.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // =====================================================
  // FORM SUBMIT
  // =====================================================

  const handleSubmit = (e) => {
    e.preventDefault();
    sendQuestion();
  };

  // =====================================================
  // ENTER KEY
  // =====================================================

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendQuestion();
    }
  };

  // =====================================================
  // NEW CHAT
  // =====================================================

  const newChat = () => {
    setQuestion("");
    setMessages([]);
    setLoading(false);
    setActiveTool(null);
  };

  const conversationStarted = messages.length > 0;

  // =====================================================
  // COLORS
  // =====================================================

  const pageBg = darkMode ? "bg-[#0f0f0f]" : "bg-white";

  const sidebarBg = darkMode ? "bg-[#151515]" : "bg-[#f7f7f7]";

  const textMain = darkMode ? "text-white" : "text-neutral-900";

  const textSecondary = darkMode ? "text-neutral-400" : "text-neutral-500";

  // =====================================================
  // UI
  // =====================================================

  return (
    <div
      className={`h-screen overflow-hidden transition-colors duration-300 ${pageBg} ${textMain}`}
    >
      <div className="flex h-screen overflow-hidden">
        {/* =================================================
            SIDEBAR
        ================================================= */}

        <aside
          className={`fixed left-0 top-0 z-30 flex h-screen w-[260px] flex-col px-4 py-5 transition-colors duration-300 ${sidebarBg}`}
        >
          {/* LOGO */}

          <div className="mb-7 flex items-center gap-3 px-2">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-xl text-base font-semibold ${
                darkMode
                  ? "bg-emerald-400 text-black"
                  : "bg-neutral-900 text-white"
              }`}
            >
              A
            </div>

            <div>
              <h1 className="text-base font-semibold">Aryan's AI</h1>

              <p className="text-xs text-neutral-500">Aryan's AI Assistant</p>
            </div>
          </div>

          {/* NEW CHAT */}

          <button
            onClick={newChat}
            className={`mb-7 flex h-11 items-center gap-3 rounded-lg border px-3 text-sm transition ${
              darkMode
                ? "border-neutral-700 text-neutral-200 hover:bg-neutral-800"
                : "border-neutral-200 text-neutral-700 hover:bg-neutral-200"
            }`}
          >
            <span className="text-xl leading-none">+</span>
            New chat
          </button>

          {/* AI TOOLS */}

          <div>
            <p
              className={`mb-3 px-2 text-[11px] font-semibold uppercase tracking-wider ${
                darkMode ? "text-neutral-500" : "text-neutral-400"
              }`}
            >
              AI Tools
            </p>

            <div className="space-y-1">
              {tools.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => setActiveTool(tool.id)}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition ${
                    activeTool === tool.id
                      ? darkMode
                        ? "bg-neutral-800 text-white"
                        : "bg-neutral-200 text-neutral-900"
                      : darkMode
                        ? "text-neutral-300 hover:bg-neutral-800"
                        : "text-neutral-600 hover:bg-neutral-200"
                  }`}
                >
                  <span
                    className={`flex w-4 justify-center ${
                      darkMode ? "text-neutral-500" : "text-neutral-400"
                    }`}
                  >
                    {tool.icon}
                  </span>

                  {tool.label}
                </button>
              ))}
            </div>
          </div>

          {/* SIDEBAR STATUS */}

          {/* SIDEBAR BOTTOM */}

          <div className="mt-auto">
            {/* STATUS */}

            <div
              className={`mb-5 flex items-center gap-2 px-2 text-xs ${textSecondary}`}
            >
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              AI assistant online
            </div>

            {/* SOCIAL LINKS */}

            <div className="flex items-center gap-5 text-gray-500">
              <a
                href="https://aryan-portfolio-eight-topaz.vercel.app/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xl transition hover:text-blue-500"
                aria-label="Portfolio"
              >
                <i className="fas fa-user-circle"></i>
              </a>

              <a
                href="https://github.com/Aryanss02"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xl transition hover:text-blue-500"
                aria-label="GitHub"
              >
                <i className="fab fa-github"></i>
              </a>

              <a
                href="https://www.linkedin.com/in/aryan-singh-708828287/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xl transition hover:text-blue-500"
                aria-label="LinkedIn"
              >
                <i className="fab fa-linkedin-in"></i>
              </a>
            </div>
          </div>
        </aside>

        {/* =================================================
            MAIN
        ================================================= */}

        <main className="ml-[260px] flex h-screen min-w-0 flex-1 flex-col">
          {/* =================================================
              FIXED HEADER
          ================================================= */}

          <header
            className={`z-20 flex h-16 shrink-0 items-center justify-between border-b px-7 transition-colors duration-300 ${
              darkMode
                ? "border-neutral-800 bg-[#0f0f0f]"
                : "border-neutral-100 bg-white"
            }`}
          >
            <div>
              <h2 className="text-sm font-semibold">
                Aryan's AI Representative
              </h2>

              <p className={`mt-0.5 text-xs ${textSecondary}`}>
                Ask questions about Aryan
              </p>
            </div>

            <div className="flex items-center gap-4">
              <button className={`text-xs ${textSecondary}`}>English⌄</button>

              <span
                className={darkMode ? "text-neutral-700" : "text-neutral-300"}
              >
                |
              </span>

              {/* DARK / LIGHT */}

              <button
                onClick={() => setDarkMode(!darkMode)}
                title={
                  darkMode ? "Switch to light mode" : "Switch to dark mode"
                }
                className={`flex h-9 w-9 items-center justify-center rounded-lg border text-base transition ${
                  darkMode
                    ? "border-neutral-600 text-yellow-300 hover:bg-neutral-800"
                    : "border-neutral-300 text-neutral-600 hover:bg-neutral-100"
                }`}
              >
                {darkMode ? "☀" : "☾"}
              </button>

              <span className="text-xs text-emerald-500">AI ●</span>
            </div>
          </header>

          {/* =================================================
              CONTENT AREA
          ================================================= */}

          <section className="flex min-h-0 flex-1 flex-col overflow-hidden">
            {/* =================================================
                SCROLLABLE CHAT / WELCOME AREA
            ================================================= */}

            <div className="min-h-0 flex-1 overflow-y-auto">
              {/* WELCOME SCREEN */}

              {!conversationStarted && (
                <div className="flex min-h-full flex-col items-center px-6 pt-28">
                  <div
                    className={`mb-5 flex h-14 w-14 items-center justify-center rounded-2xl text-base font-semibold shadow-sm ${
                      darkMode
                        ? "bg-emerald-400 text-black"
                        : "bg-neutral-900 text-white"
                    }`}
                  >
                    A
                  </div>

                  <h1 className="text-4xl font-semibold tracking-tight">
                    How can I help you?
                  </h1>

                  <p
                    className={`mt-3 max-w-lg text-center text-sm leading-6 ${textSecondary}`}
                  >
                    Ask about Aryan's education, skills, projects, experience,
                    certifications or resume.
                  </p>

                  <div className="mt-8 grid w-full max-w-[700px] grid-cols-2 gap-3 pb-8">
                    {suggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => sendQuestion(suggestion)}
                        className={`group flex min-h-[58px] items-center justify-between rounded-xl border px-4 py-3 text-left text-sm transition ${
                          darkMode
                            ? "border-neutral-800 bg-[#141414] hover:border-neutral-700 hover:bg-neutral-900"
                            : "border-neutral-200 bg-white hover:border-neutral-300 hover:bg-neutral-50"
                        }`}
                      >
                        <span>{suggestion}</span>

                        <span
                          className={`ml-3 text-base transition ${
                            darkMode
                              ? "text-neutral-600 group-hover:text-neutral-300"
                              : "text-neutral-400 group-hover:text-neutral-700"
                          }`}
                        >
                          ↗
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* CONVERSATION */}

              {conversationStarted && (
                <div className="px-6 py-8">
                  <div className="mx-auto w-full max-w-[850px] space-y-8 pb-6">
                    {messages.map((message, index) => {
                      const isUser = message.role === "user";

                      return (
                        <div
                          key={index}
                          className={`flex w-full ${
                            isUser ? "justify-end" : "justify-start"
                          }`}
                        >
                          <div
                            className={`max-w-[75%] ${
                              isUser ? "items-end" : "items-start"
                            }`}
                          >
                            {/* LABEL */}

                            <div
                              className={`mb-2 text-xs font-medium ${
                                isUser
                                  ? darkMode
                                    ? "text-right text-neutral-500"
                                    : "text-right text-neutral-400"
                                  : "text-emerald-500"
                              }`}
                            >
                              {isUser ? "You" : "Aryan's AI"}
                            </div>

                            {/* MESSAGE */}

                            <div
                              className={`whitespace-pre-wrap text-sm leading-7 ${
                                isUser
                                  ? darkMode
                                    ? "rounded-2xl rounded-br-md bg-neutral-800 px-5 py-3 text-neutral-100"
                                    : "rounded-2xl rounded-br-md bg-neutral-100 px-5 py-3 text-neutral-800"
                                  : darkMode
                                    ? "text-neutral-300"
                                    : "text-neutral-700"
                              }`}
                            >
                              {renderMessage(message.content)}
                            </div>
                          </div>
                        </div>
                      );
                    })}

                    {/* LOADING */}

                    {loading && (
                      <div className="flex justify-start">
                        <div>
                          <div className="mb-2 text-xs font-medium text-emerald-500">
                            Aryan's AI
                          </div>

                          <div className="flex items-center gap-1.5 py-2">
                            <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-400" />

                            <span
                              className="h-2 w-2 animate-bounce rounded-full bg-neutral-400"
                              style={{
                                animationDelay: "0.15s",
                              }}
                            />

                            <span
                              className="h-2 w-2 animate-bounce rounded-full bg-neutral-400"
                              style={{
                                animationDelay: "0.3s",
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    )}

                    <div ref={messagesEndRef} />
                  </div>
                </div>
              )}
            </div>

            {/* =================================================
                FIXED SEARCH BAR
            ================================================= */}

            <div
              className={`shrink-0 border-t px-6 pb-6 pt-4 ${
                darkMode
                  ? "border-neutral-800 bg-[#0f0f0f]"
                  : "border-neutral-100 bg-white"
              }`}
            >
              <div className="mx-auto max-w-[850px]">
                <form
                  onSubmit={handleSubmit}
                  className={`flex items-center rounded-2xl border p-1.5 shadow-sm transition ${
                    darkMode
                      ? "border-neutral-800 bg-[#171717]"
                      : "border-neutral-200 bg-white"
                  }`}
                >
                  <span
                    className={`px-4 text-lg ${
                      darkMode ? "text-neutral-500" : "text-neutral-400"
                    }`}
                  >
                    ⌕
                  </span>

                  <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={loading}
                    placeholder="Ask anything about Aryan..."
                    className={`flex-1 bg-transparent px-1 py-3.5 text-sm outline-none ${
                      darkMode
                        ? "text-white placeholder:text-neutral-600"
                        : "text-neutral-900 placeholder:text-neutral-400"
                    }`}
                  />

                  <button
                    type="submit"
                    disabled={loading || !question.trim()}
                    className={`flex h-10 w-10 items-center justify-center rounded-xl text-base transition ${
                      loading || !question.trim()
                        ? "cursor-not-allowed opacity-40"
                        : darkMode
                          ? "bg-white text-black hover:bg-neutral-200"
                          : "bg-neutral-900 text-white hover:bg-neutral-700"
                    }`}
                  >
                    {loading ? "..." : "↑"}
                  </button>
                </form>

                <p
                  className={`mt-3 text-center text-[10px] ${
                    darkMode ? "text-neutral-600" : "text-neutral-400"
                  }`}
                >
                  AI answers are generated using Aryan's resume.
                </p>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
