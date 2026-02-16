export default function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-2">
        <span className="inline-block w-2 h-2 bg-black rounded-full" />
        <span className="text-sm text-text-primary">
          Recupero le informazioni, attendi..
        </span>
      </div>
    </div>
  );
}
