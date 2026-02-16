import { WARNING_TEXT } from '../../utils/messageClassifier';

export default function WarningBanner() {
  return (
    <div className="bg-warning-bg border border-warning/30 rounded-lg px-3 py-2 flex items-start gap-2">
      <span className="text-warning text-base leading-none mt-0.5">&#9888;</span>
      <p className="text-xs text-amber-800">{WARNING_TEXT}</p>
    </div>
  );
}
