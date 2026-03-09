import avatarImg from '../../assets/avatar-nurse.svg';

export default function ChatEmptyState({ userName }) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 text-center px-4">
      <img
        src={avatarImg}
        alt="Avatar"
        className="w-20 h-20 rounded-full mb-4 object-cover"
      />
      <h2 className="text-xl font-semibold text-gray-800">
        Buongiorno {userName}
      </h2>
      <p className="text-gray-500 mt-1">Come posso aiutarti?</p>
    </div>
  );
}
