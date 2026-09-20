import { useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { IdCard, RefreshCw, Printer } from "lucide-react";
import { useTheme, surface, accentText } from "../../theme/ThemeContext";
import { Panel, Badge } from "../../components/ui";
import Breadcrumb from "../../components/Breadcrumb";
import {
  generateMockBeneficiary,
  buildBeneficiaryPayload,
} from "../../utils/mockAadhaar";

export default function BeneficiaryCard() {
  const { theme } = useTheme();
  const s = surface(theme);

  const [card, setCard] = useState(() => {
    const b = generateMockBeneficiary();
    return { ...b, payload: buildBeneficiaryPayload(b.id, b.name) };
  });

  function handleGenerate() {
    const b = generateMockBeneficiary();
    setCard({ ...b, payload: buildBeneficiaryPayload(b.id, b.name) });
  }

  function handlePrint() {
    window.print();
  }

  const qrValue = JSON.stringify(card.payload);

  return (
    <div>
      <Breadcrumb trail={["Dashboard", "Funds", "ID Card"]} />
      <div className="p-5 max-w-lg mx-auto space-y-4">
        <Panel
          title="Mock Beneficiary Card"
          icon={IdCard}
          accent="violet"
          right={
            <button
              onClick={handleGenerate}
              className={`flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest ${accentText(theme, "violet")} opacity-70 hover:opacity-100`}
            >
              <RefreshCw className="w-3 h-3" />
              new card
            </button>
          }
        >
          <div
            id="beneficiary-card-print"
            className={`flex flex-col items-center gap-4 p-5 rounded border border-white/10 ${s.panel}`}
          >
            <div className="bg-white p-3 rounded">
              <QRCodeSVG value={qrValue} size={180} />
            </div>

            <div className="text-center space-y-1">
              <div className={`text-sm font-mono ${s.textPrimary}`}>
                {card.name}
              </div>
              <div className={`text-xs font-mono ${s.textSecondary}`}>
                Mock ID: {card.id}
              </div>
              <div className={`text-[10px] font-mono ${s.textSecondary}`}>
                Issued: {card.payload.issued}
              </div>
              <Badge className="bg-amber-500/10 text-amber-400 border border-amber-400/30 mt-1">
                simulation only — not a real ID
              </Badge>
            </div>
          </div>

          <button
            onClick={handlePrint}
            className={`mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 rounded text-xs font-mono uppercase tracking-widest border ${accentText(theme, "violet")} border-violet-400/30 hover:bg-violet-400/10`}
          >
            <Printer className="w-3.5 h-3.5" />
            print card
          </button>
        </Panel>
      </div>
    </div>
  );
}
