// In your Next.js page
import ImageCDN from './components/image-cdn';

const MyPage = () => {
  // Define your custom styles
  const customStyles = {
    width: '300px',
    borderRadius: '10px',
    // Add more styles as needed
  };

  return (
    <div>
      <h1>My Page</h1>
      <ImageCDN
        imageUrl="https://images.pexels.com/photos/1089930/pexels-photo-1089930.jpeg"
        size="large"
        style={customStyles}
      />
    </div>
  );
};

export default MyPage;
