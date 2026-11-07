import Navbar from '../components/Navbar';
import { useAuth } from '../AuthContext';

export default function Home() {
  const { user } = useAuth();
  return (
    <>
      <Navbar />
      <main className="center">
        <h1>Bine ai venit, {user?.first_name}!</h1>
        <p>Aici vor apărea ofertele tale personalizate.</p>
      </main>
    </>
  );
}