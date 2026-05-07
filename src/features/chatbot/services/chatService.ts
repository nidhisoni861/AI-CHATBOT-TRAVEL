export async function sendMessageToApi(message: string): Promise<{ reply: string }> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error("Network error");
  return (await res.json()) as { reply: string };
}
