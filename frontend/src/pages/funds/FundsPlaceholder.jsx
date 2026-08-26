import { Landmark } from "lucide-react";
import { useTheme, surface, accentText } from "../../theme/ThemeContext";
import { Panel } from "../../components/ui";
import Breadcrumb from "../../components/Breadcrumb";

export default function FundsPlaceholder() {
  const { theme } = useTheme();
  const s = surface(theme);
  return (
    <div>
      <Breadcrumb trail={["Dashboard", "Funds"]} />
      <div className="p-5 max-w-4xl mx-auto">
        <Panel title="Blockchain / Fund Ledger" icon={Landmark} accent="cyan">
          <p className={`text-sm font-mono ${s.textSecondary}`}>
            will start soon ig
          </p>
        </Panel>
      </div>
    </div>
  );
}
