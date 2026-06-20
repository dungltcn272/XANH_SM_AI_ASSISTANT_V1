import { Link2, CheckCheck, ThumbsUp, ThumbsDown, ShieldCheck } from 'lucide-react';
import { FoodLocationRequestCard, FoodLocationConfirmedCard } from './FoodLocationPrompt';
import { FoodRecommendationList } from './FoodInlineCards';

export const MessageBubble = ({
  msg,
  idx,
  loading,
  formatTime,
  renderContent,
  renderFoodInlineParts,
  handleUseCurrentFoodLocation,
  handleSubmitFoodAddress,
  handleSelectMapFoodLocation,
  savedFoodLocations,
  handleSaveNamedFoodLocation,
  logFoodInteraction,
  setMessages,
  setExplainingFood,
  RagCardList,
  handleReviewClick,
  submittedReviews
}) => {
  const hasAssistantPayload = Boolean(
    msg.content ||
    msg.foodLocationRequest ||
    msg.foodLocationConfirmed ||
    msg.foodInlineParts ||
    msg.foodRecommendations ||
    msg.ragCards ||
    (msg.sources && msg.sources.length > 0)
  );

  if (msg.role === 'assistant' && (!hasAssistantPayload || (!msg.content && loading))) return null;

  return (
    <div className={`flex flex-col w-full ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
      {/* Header info */}
      <div className={`flex items-center gap-2 mb-2 px-1 text-[11px] font-bold text-on-surface-variant/50 select-none ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
        {msg.role === 'user' ? (
          <>
            <span>Bạn</span>
            <span>⬢</span>
            <span>{formatTime(msg.created_at)}</span>
          </>
        ) : (
          <>
            <span className="text-[#00c897]">Xanh SM</span>
            <div className="px-1.5 py-0.5 rounded-md border border-[#00c897]/30 text-[#00c897] scale-75 origin-left flex items-center justify-center font-black">AI</div>
            <span>⬢</span>
            <span>{formatTime(msg.created_at)}</span>
          </>
        )}
      </div>

      <div className={`flex gap-3 w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'} items-start`}>
        {msg.role !== 'user' && (
          <div className="w-10 h-10 rounded-full bg-white dark:bg-white/10 flex items-center justify-center text-white shrink-0 shadow-md border border-[#00c897]/20 relative overflow-hidden group">
            <img src="/Bot.png" alt="Xanh SM AI" className="w-7 h-7 object-contain group-hover:scale-110 transition-transform" />
          </div>
        )}
        
        <div className={`${msg.role === 'user' ? 'order-1 max-w-[85%]' : 'order-2 max-w-[calc(100%_-_3.25rem)] md:max-w-[85%]'}`}>
          <div className={`p-4 md:p-5 rounded-3xl text-sm md:text-base leading-relaxed transition-all duration-300 flex flex-col gap-4 ${
            msg.role === 'user' 
              ? 'bg-gradient-to-br from-[#00c897] to-[#009e79] text-white rounded-tr-none shadow-[0_4px_16px_rgba(0,200,151,0.15)] dark:shadow-[0_4px_16px_rgba(0,200,151,0.05)] border border-[#00c897]/20' 
              : 'bg-white/88 dark:bg-white/5 backdrop-blur-md border border-white/40 dark:border-white/10 text-on-surface rounded-tl-none shadow-[0_8px_30px_rgba(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgba(0,0,0,0.2)]'
          }`}>
            {msg.role === 'user' ? (
              <div className="flex flex-col gap-2">
                {msg.image && (
                  <img src={msg.image} alt="User upload" className="max-w-[200px] max-h-[200px] rounded-xl object-contain bg-black/20" />
                )}
                <p className="whitespace-pre-wrap font-medium">{msg.content}</p>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                {msg.foodInlineParts ? (
                  renderFoodInlineParts(msg, idx)
                ) : msg.content && (
                  <div className="prose prose-sm md:prose-base dark:prose-invert max-w-none">
                    {renderContent(msg.content)}
                  </div>
                )}
                {msg.foodLocationRequest && (
                  <FoodLocationRequestCard
                    request={msg.foodLocationRequest}
                    onUseCurrentLocation={() => handleUseCurrentFoodLocation(msg.foodLocationRequest)}
                    onSubmitAddress={(address) => handleSubmitFoodAddress(msg.foodLocationRequest, address)}
                    onSelectMapLocation={(pin) => handleSelectMapFoodLocation(msg.foodLocationRequest, pin)}
                    savedLocations={savedFoodLocations}
                  />
                )}
                {msg.foodLocationConfirmed && (
                  <FoodLocationConfirmedCard
                    location={msg.foodLocationConfirmed}
                    onSaveNamedLocation={handleSaveNamedFoodLocation}
                  />
                )}
                {msg.foodRecommendations && !msg.foodInlineParts && (
                    <FoodRecommendationList
                      data={msg.foodRecommendations}
                      onOpenMenu={(item, rankPosition) => {
                        logFoodInteraction('click_item', item, rankPosition, msg.foodRecommendations, msg);
                        logFoodInteraction('click_out', item, rankPosition, msg.foodRecommendations, msg);
                      }}
                      onLike={(item, rankPosition) => {
                        setMessages(prev => prev.map(m => m.id === msg.id ? {
                          ...m,
                          foodRecommendations: {
                            ...m.foodRecommendations,
                            items: m.foodRecommendations.items.map(i => i.item_id === item.item_id ? { ...i, interaction: i.interaction === 'like' ? null : 'like' } : i)
                          }
                        } : m));
                        logFoodInteraction('like', item, rankPosition, msg.foodRecommendations, msg);
                      }}
                      onDismiss={(item, rankPosition) => {
                        setMessages(prev => prev.map(m => m.id === msg.id ? {
                          ...m,
                          foodRecommendations: {
                            ...m.foodRecommendations,
                            items: m.foodRecommendations.items.filter(i => i.item_id !== item.item_id)
                          }
                        } : m));
                        logFoodInteraction('dismiss', item, rankPosition, msg.foodRecommendations, msg);
                      }}
                      onDislike={(item, rankPosition) => {
                        setMessages(prev => prev.map(m => m.id === msg.id ? {
                          ...m,
                          foodRecommendations: {
                            ...m.foodRecommendations,
                            items: m.foodRecommendations.items.map(i => i.item_id === item.item_id ? { ...i, interaction: i.interaction === 'dislike' ? null : 'dislike' } : i)
                          }
                        } : m));
                        logFoodInteraction('dislike', item, rankPosition, msg.foodRecommendations, msg);
                      }}
                      onExplain={(item) => setExplainingFood(item)}
                    />
                )}
                {msg.ragCards && RagCardList && (
                  <RagCardList cards={msg.ragCards} />
                )}
              </div>
            )}
            
            {/* Citations / Sources */}
            {msg.sources && msg.sources.length > 0 && (() => {
              const uniqueSources = [];
              const seenSources = new Set();
              for (const src of msg.sources) {
                const normalizedSource = (src.source || '').toLowerCase().trim();
                if (normalizedSource && !seenSources.has(normalizedSource)) {
                  seenSources.add(normalizedSource);
                  uniqueSources.push(src);
                }
              }
              return (
                <div className="flex gap-2 flex-wrap mt-1">
                  {uniqueSources.slice(0, 3).map((src, i) => (
                    <a key={i} href={src.url || '#'} target="_blank" rel="noopener noreferrer" 
                       className="flex items-center gap-1 text-[10px] font-bold bg-surface-container-high/50 text-primary px-3 py-1.5 rounded-full border border-primary/20 hover:bg-primary hover:text-white transition-all max-w-[240px]">
                      <Link2 size={10} className="shrink-0" />
                      <span className="truncate">
                        {src.source ? src.source.replace(/\.(md|html|txt)$/i, '').replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Tài liệu Xanh SM'}
                      </span>
                    </a>
                  ))}
                </div>
              );
            })()}

            {/* Assistant Footer */}
            {msg.role === 'assistant' && (
              <div className="mt-2 pt-3 border-t border-outline-variant/10 flex items-center justify-between text-[10px] font-bold text-on-surface-variant/40">
                <div className="flex items-center gap-1.5">
                  <span className="scale-110">⏱️</span>
                  <span>Tổng thời gian: {msg.latency_ms ? `${Math.round(msg.latency_ms)}ms` : 'N/A'}</span>
                </div>
                <div className="flex items-center gap-3">
                  {msg.id && handleReviewClick && submittedReviews && (
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => handleReviewClick(msg.id, 'up')}
                        className={`hover:text-[#00c897] transition-colors p-1 rounded-md ${submittedReviews[msg.id] === 'up' ? 'text-[#00c897] bg-[#00c897]/10' : ''}`}
                        title="Hữu ích"
                        disabled={!!submittedReviews[msg.id]}
                      >
                        <ThumbsUp size={14} />
                      </button>
                      <button 
                        onClick={() => handleReviewClick(msg.id, 'down')}
                        className={`hover:text-red-500 transition-colors p-1 rounded-md ${submittedReviews[msg.id] === 'down' ? 'text-red-500 bg-red-50' : ''}`}
                        title="Không hữu ích"
                        disabled={!!submittedReviews[msg.id]}
                      >
                        <ThumbsDown size={14} />
                      </button>
                    </div>
                  )}
                  <div className="flex items-center gap-1.5">
                    <span>Nguồn: Xanh SM Official</span>
                    <ShieldCheck size={12} className="text-[#00c897]" />
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {msg.role === 'user' && (
            <div className="flex justify-end mt-1.5 px-1">
              <CheckCheck size={14} className="text-[#00c897]" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
