import React, { useState } from 'react';

function SearchForm({ onSearch }) {
  const [searchParams, setSearchParams] = useState({
    ticker: '',
    date: '',
  });

  const handleChange = (e) => {
    setSearchParams({ ...searchParams, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(searchParams);
  };

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="form-group">
        <label htmlFor="ticker">Ticker:</label>
        <input
          type="text"
          id="ticker"
          name="ticker"
          value={searchParams.ticker}
          onChange={handleChange}
        />
      </div>
      <div className="form-group">
        <label htmlFor="date">Date:</label>
        <input
          type="date"
          id="date"
          name="date"
          value={searchParams.date}
          onChange={handleChange}
        />
      </div>

      <button type="submit">Search</button>
    </form>
  );
}

export default SearchForm;
