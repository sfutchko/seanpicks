import React from 'react';
import './HelpModal.css';

const HelpModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="help-modal-overlay" onClick={onClose}>
      <div className="help-modal-content" onClick={e => e.stopPropagation()}>
        <div className="help-modal-header">
          <h2>How to Read the Picks</h2>
          <button className="help-close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="help-modal-body">
          <section className="help-section">
            <h3>Understanding the Lines</h3>
            <dl>
              <dt>Spread (e.g., -8.5)</dt>
              <dd>The point spread. Negative means favorite (must win by more than that number). Positive means underdog (can lose by less than that number).</dd>
              
              <dt>Money Line (e.g., -450/+330)</dt>
              <dd>Straight up win/loss bet. Negative number = favorite (bet that amount to win $100). Positive = underdog (bet $100 to win that amount).</dd>
              
              <dt>O/U (Over/Under)</dt>
              <dd>Total combined points scored by both teams. Bet whether actual total will be over or under this number.</dd>
            </dl>
          </section>

          <section className="help-section">
            <h3>Key Indicators</h3>
            <dl>
              <dt>Sharp Money %</dt>
              <dd>Professional bettors' money movement. Higher % means more sharp money on this side. Example: +18.3% means pros are heavily backing this team.</dd>
              
              <dt>Fade Public %</dt>
              <dd>Going against casual bettors. Example: +2% means slight advantage in betting opposite of the public majority.</dd>
              
              <dt>Steam Move</dt>
              <dd>Rapid line movement across multiple sportsbooks, indicating coordinated sharp action.</dd>
              
              <dt>Injury Edge</dt>
              <dd>Advantage based on key player injuries. Positive % means injuries favor this pick.</dd>
              
              <dt>Line Value</dt>
              <dd>Current line compared to predicted fair value. Positive % means you're getting better odds than expected.</dd>
              
              <dt>Situational Edge</dt>
              <dd>Factors like rest days, travel, revenge games. Higher % means stronger situational advantage.</dd>
            </dl>
          </section>

          <section className="help-section">
            <h3>Confidence Levels</h3>
            <dl>
              <dt>55%+ Confidence</dt>
              <dd>Strong play - Recommended bet size: 3-4% of bankroll</dd>
              
              <dt>52-54% Confidence</dt>
              <dd>Standard play - Recommended bet size: 2-3% of bankroll</dd>
              
              <dt>50-51% Confidence</dt>
              <dd>Lean only - Recommended bet size: 1% of bankroll or pass</dd>
            </dl>
          </section>

          <section className="help-section">
            <h3>Kelly Criterion</h3>
            <p>The Kelly % shows optimal bet sizing based on edge and confidence. We recommend using 30% Kelly (more conservative) to protect your bankroll.</p>
            <p>Example: If Kelly says bet 10% of bankroll, we recommend 3% (30% of Kelly).</p>
          </section>

          <section className="help-section">
            <h3>Best Practices</h3>
            <ul>
              <li>Never bet more than 5% of your bankroll on a single game</li>
              <li>Track all your bets to identify patterns</li>
              <li>Shop for the best lines across multiple sportsbooks</li>
              <li>Avoid parlays unless specifically recommended</li>
              <li>Don't chase losses - stick to the system</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
};

export default HelpModal;