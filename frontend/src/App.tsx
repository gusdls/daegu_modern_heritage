import axios from "axios";
import { useEffect, useState } from "react";

interface Review {
  id: number;
  location: string;
  score: number;
  timestamp: string;
}

function App() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const getReviews = async () => {
    const response = await axios.get("http://localhost:8000/scores/");
    console.log(response.data);
    if (response.status != 200) return;
    setReviews(response.data.scores);
  };
  useEffect(() => {
    getReviews();
  }, []);
  return (
    <div>
      <ul>
        {reviews.map((review) => (
          <li key={review.id}>
            {review.location} {review.score}점 {review.timestamp}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
