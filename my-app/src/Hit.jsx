import React from 'react';
import PropTypes from 'prop-types';
import { Highlight } from 'react-instantsearch-dom';

export const Hit = ({ hit }) => {
  return (
    <article>
      <div className="hit">
        <div className="hit-field">
          <strong>Domain:</strong> <Highlight attribute="domain" hit={hit} />
        </div>
        <div className="hit-field">
          <strong>Available Names:</strong> <Highlight attribute="Company All Available Names" hit={hit} />
        </div>
        <div className="hit-field">
          <strong>Commercial Name:</strong> <Highlight attribute="Company Commercial Name" hit={hit} />
        </div>
        <div className="hit-field">
          <strong>Legal Name:</strong> <Highlight attribute="Company Legal Name" hit={hit} />
        </div>
        <div className="hit-field">
          <strong>Address:</strong> <Highlight attribute="addresses" hit={hit} />
        </div>
        <div className="hit-field">
          <strong>Facebook:</strong> <Highlight attribute="facebook_links" hit={hit} />
        </div>
        <div className="hit-field">
          <strong>Phone:</strong> <Highlight attribute="phone_numbers" hit={hit} />
        </div>
      </div>
    </article>
  );
};

Hit.propTypes = {
  hit: PropTypes.object.isRequired, 
};