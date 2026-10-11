import Link from "next/link";

const samplePets = [
  { id: "pet-1", name: "Milo", type: "Dog", age: "3 years" },
  { id: "pet-2", name: "Luna", type: "Cat", age: "2 years" },
];

export default function PetsPage() {
  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-600">Pet profiles</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Your pets</h1>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {samplePets.map((pet) => (
          <Link
            key={pet.id}
            href={`/pets/${pet.id}`}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-300 hover:shadow-md"
          >
            <div className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-500">{pet.type}</div>
            <h2 className="mt-2 text-2xl font-semibold text-slate-900">{pet.name}</h2>
            <p className="mt-2 text-slate-600">Age: {pet.age}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
