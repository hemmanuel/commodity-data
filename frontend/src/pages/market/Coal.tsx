import MarketOverview from '../../components/MarketOverview';

const Coal = () => {
  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="border-b border-gray-700 pb-4">
        <h2 className="text-2xl font-bold text-white">Coal Market</h2>
      </div>
      <div className="flex-1 min-h-0">
        <MarketOverview category="coal" />
      </div>
    </div>
  );
};

export default Coal;
