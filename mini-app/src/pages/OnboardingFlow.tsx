import { Bell, HeartHandshake, Sparkles } from "lucide-react";

import { Button } from "../components/Button";
import { Card } from "../components/Card";

type OnboardingFlowProps = {
  onDone: () => void;
};

export const OnboardingFlow = ({ onDone }: OnboardingFlowProps) => (
  <div className="page-stack onboarding-page">
    <section className="hero-panel">
      <div>
        <span className="soft-label">Zarina Rise</span>
        <h1>Мягкий ритм дня</h1>
        <p className="hero-copy">Еда, вода, фокус, дневник и сон — маленькими шагами.</p>
      </div>
      <div className="hero-mark" aria-hidden="true">
        <Sparkles size={26} />
      </div>
    </section>

    <Card className="onboarding-card">
      <HeartHandshake size={26} />
      <h2>Маленькие шаги</h2>
      <p>Еда, вода, фокус, дневник, сон и тёплые сообщения собираются в спокойный ритм.</p>
    </Card>

    <Card className="onboarding-card">
      <Bell size={26} />
      <h2>Без давления</h2>
      <p>Напоминания можно поставить на паузу. Пропуски не превращаются в оценку.</p>
    </Card>

    <Button onClick={onDone}>
      <Sparkles size={18} />
      Начать день мягко
    </Button>
  </div>
);
