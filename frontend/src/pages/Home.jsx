import Navbar from '../components/Navbar';
import { useAuth } from '../AuthContext';
import { Link } from 'react-router-dom';

export default function Home() {
  const { user } = useAuth();
  return (
    <>
      <Navbar />
      <main className="center">
        <h1>Bine ai venit, {user?.first_name}!</h1>
        <p>Aici vor apărea ofertele tale personalizate.</p>
        <Link className="subscription-link" to="/subscriptions">
          Gestionează abonamentele la branduri
        </Link>
      </main>
    </>
  );
}