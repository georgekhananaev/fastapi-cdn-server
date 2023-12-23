// ImageCDN.js
import React, { useState, useEffect } from 'react';

const ImageCDN = ({ imageUrl, size, style }) => {
    const [displayUrl, setDisplayUrl] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const cacheImageUrl = async () => {
            try {
                const response = await fetch(`http://localhost:8080/cache_url?overwrite=false`, {
                    method: 'POST',
                    headers: {
                        'accept': 'application/json',
                        'Authorization': 'Bearer 123456789',
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams({ url: imageUrl })
                });

                if (response.ok) {
                    const data = await response.json();
                    const sizeUrl = data.cachedUrls.find(url => url.includes(`/${size}_`));
                    setDisplayUrl(`http://localhost:8080/${sizeUrl}`);
                } else {
                    console.error('Error caching image:', response.statusText);
                }
            } catch (error) {
                console.error('Error caching image:', error);
            } finally {
                setLoading(false);
            }
        };

        if (imageUrl && size) {
            cacheImageUrl();
        }
    }, [imageUrl, size]);

    if (loading) {
        return <div>Loading image...</div>;
    }

    return displayUrl ? <img src={displayUrl} style={style} alt="Fetched" /> : <div>Image not available</div>;
};

export default ImageCDN;
