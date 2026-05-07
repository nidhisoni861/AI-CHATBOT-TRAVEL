export type Message = {
  id: string;
  role: "user" | "bot";
  text: string;
  createdAt: string;
};

export type Chat = {
  id: string;
  title?: string;
  messages: Message[];
  createdAt: string;
};
