import ReactMarkdown from 'react-markdown';
import { classifyMessage } from '../../utils/messageClassifier';
import WarningBanner from './WarningBanner';
import ErrorBanner from './ErrorBanner';
import ResponseActions from './ResponseActions';

export default function ChatBubble({ message }) {
  const { role, content, patientContext } = message;
  const isUser = role === 'user';
  const classification = !isUser
    ? classifyMessage(content, patientContext)
    : 'normal';

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="bg-[#F4F7FA] text-text-primary px-4 py-3 rounded-t-2xl rounded-bl-2xl max-w-[80%]">
          <p className="text-sm leading-relaxed">{content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-2">
        {classification === 'warning' && <WarningBanner />}
        {classification === 'error' && <ErrorBanner />}
        <div className="bg-white px-4 py-3 rounded-t-2xl rounded-br-2xl shadow-[0_1px_4px_rgba(0,0,0,0.08)]">
          <div className="text-sm text-gray-800 leading-relaxed [&_ul]:my-1 [&_ol]:my-1 [&_li]:my-0.5 [&_p]:my-1 [&_p:first-child]:mt-0 [&_p:last-child]:mb-0 [&_strong]:text-gray-900 [&_ul]:pl-4 [&_ol]:pl-4">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>
        <ResponseActions content={content} />
      </div>
    </div>
  );
}
