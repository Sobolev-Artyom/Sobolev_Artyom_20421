'use client'
import { Grid } from "@giphy/react-components";
import { GiphyFetch } from '@giphy/js-fetch-api';
import { useState, useEffect } from "react";

// API Ключ Giphy
const gf = new GiphyFetch('wLtsStJrYmAEYU7OezJwNvf7My71ZKsq');

export default function Home() {
  const [messages, setMessages] = useState<string[]>([]);
  const [inputText, setInputText] = useState('');
  const [isGifMenuOpen, setGifMenuOpen] = useState(false);
  const [gifSearchText, setGifSearchText] = useState('');
  const [debouncedSearchText, setDebouncedSearchText] = useState('');
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setGifSearchText(debouncedSearchText);
    }, 500); 
    return () => clearTimeout(timer);
  }, [debouncedSearchText]);

  useEffect(() => {
    if (gifSearchText.trim()) {
      setGifMenuOpen(true);
    } else {
      setGifMenuOpen(false);
    }
  }, [gifSearchText]);

  const fetchGifs = (offset: number) => gf.search(gifSearchText, { offset, limit: 10 });

  const handleSendMessage = () => {
    if (inputText.trim() && !inputText.startsWith('/gif')) {
      setMessages((prev) => [...prev, inputText.trim()]);
      setInputText('');
    }
  };

  const handleGifSelect = (gifUrl: string) => {
    setMessages((prev) => [...prev, gifUrl]);
    setGifMenuOpen(false);
    setInputText('');
  };

  const handleInputChange = (text: string) => {
    setInputText(text);

    if (text.startsWith('/gif ')) {
      const searchQuery = text.replace('/gif ', '').trim();
      setDebouncedSearchText(searchQuery);
    } else {
      setGifMenuOpen(false);
    }
  }; 

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  const getCurrentTime = () => {
    const currentTime = new Date();
    return currentTime
  };


  return (
  <div className="chat-container">
    <div className="messages-container">
    {isGifMenuOpen && (
      <div className="gif-menu">
        <Grid
          width={380}
          columns={3}
          fetchGifs={fetchGifs}
          onGifClick={(gif, e) => {
            e.preventDefault();
            handleGifSelect(gif.images.fixed_height.url);
          }}
        />
      </div>
    )}
      {messages.map((msg, index) => (
        <div key={index} className="message">
          {msg.startsWith('http') ? (
            <table>
              <tbody>
                <tr>
                  <td><img src={msg} alt="GIF" className="gif-image" /></td>
                  <td style={{position: 'relative'}}><p className="timestamp" style={{bottom: '0', position:'absolute'}}>{getCurrentTime().getHours()}:{(getCurrentTime().getMinutes() < 10 ? '0' : '') + getCurrentTime().getMinutes()}</p></td>
                </tr>
              </tbody>
            </table>
          ) : (
            <table>
              <tbody>
                <tr>
                  <td><p>{msg}</p></td>
                  <td><p className="timestamp">{getCurrentTime().getHours()}:{(getCurrentTime().getMinutes() < 10 ? '0' : '') + getCurrentTime().getMinutes()}</p></td>
                </tr>
              </tbody>
            </table>
          )}
        </div>
      ))}
    </div>

    <div className="input-container">
      <div className="colored-gif-div" style={{ visibility: inputText.startsWith('/gif') ? 'visible' : 'hidden' }}>
      <span className="colored-gif">/gif</span></div>
      <input
        type="text"
        value={inputText}
        placeholder="Напишите сообщение..."
        onChange={(e) => handleInputChange(e.target.value)}
        onKeyDown={handleKeyDown}
        className="text-input"
      />
    </div>
  </div>
  );
}
