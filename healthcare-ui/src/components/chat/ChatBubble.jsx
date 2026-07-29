import ReactMarkdown from 'react-markdown';
import { classifyMessage } from '../../utils/messageClassifier';
import WarningBanner from './WarningBanner';
import ErrorBanner from './ErrorBanner';
import ResponseActions from './ResponseActions';
import avatarImg from '../../assets/avatar-nurse.svg';

function UserAvatar() {
  return (
    <div className="w-8 h-8 rounded-full bg-navy text-white flex items-center justify-center shrink-0">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    </div>
  );
}

export default function ChatBubble({ message }) {
  const { role, content, patientContext } = message;
  const isUser = role === 'user';
  const classification = !isUser
    ? classifyMessage(content, patientContext)
    : 'normal';

  if (isUser) {
    return (
      <div className="flex justify-end items-end gap-2 animate-slide-up">
        <div className="bg-teal/10 text-text-primary px-4 py-3 rounded-t-2xl rounded-bl-2xl max-w-[80%] border border-teal/10">
          <p className="text-sm leading-relaxed">{content}</p>
        </div>
        <UserAvatar />
      </div>
    );
  }

  return (
    <div className="flex justify-start items-end gap-2 animate-slide-up">
      <img src={avatarImg} alt="Assistant" className="w-8 h-8 rounded-full object-cover shrink-0" />
      <div className="max-w-[85%] space-y-2">
        {classification === 'warning' && <WarningBanner />}
        {classification === 'error' && <ErrorBanner />}
        <div className="bg-gray-50 px-4 py-3 rounded-t-2xl rounded-br-2xl border border-gray-100">
          <div className="text-sm text-gray-800 leading-relaxed [&_ul]:my-1 [&_ol]:my-1 [&_li]:my-0.5 [&_p]:my-1 [&_p:first-child]:mt-0 [&_p:last-child]:mb-0 [&_strong]:text-gray-900 [&_ul]:pl-4 [&_ol]:pl-4">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>
        <ResponseActions content={content} />
      </div>
    </div>
  );
}
