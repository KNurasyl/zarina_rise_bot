import { MessageCircleHeart } from "lucide-react";

import { Card } from "../components/Card";

export const OutsideTelegramPage = () => (
  <div className="outside-shell">
    <Card className="outside-card">
      <MessageCircleHeart size={34} />
      <h1>Открой Zarina Rise в Telegram</h1>
      <p>Личные данные доступны только внутри Telegram Mini App.</p>
    </Card>
  </div>
);
