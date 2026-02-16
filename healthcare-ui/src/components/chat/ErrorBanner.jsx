import { ERROR_TEXT } from '../../utils/messageClassifier';

export default function ErrorBanner() {
  return (
    <div className="bg-error-bg border border-error/30 rounded-lg px-3 py-2 flex items-start gap-2">
      <span className="text-error text-base leading-none mt-0.5">&#9679;</span>
      <p className="text-xs text-red-800">{ERROR_TEXT}</p>
    </div>
  );
}
