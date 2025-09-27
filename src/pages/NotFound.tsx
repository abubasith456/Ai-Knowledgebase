import { useNavigate } from 'react-router-dom';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-white text-gray-800 px-4">
      <div className="text-center space-y-6">
        <h1 className="text-6xl font-bold text-gray-500">404</h1>
        <p className="text-2xl  font-semibold">Page Not Found</p>
        <p className="text-gray-600">
          The page you're looking for doesn’t exist or has been moved.
        </p>
        <button
          onClick={() => navigate('/')}
          className='cursor-pointer'
        >
          Go to Home
        </button>
      </div>
    </div>
  );
};

export default NotFound;
