import algoliasearch from 'algoliasearch/lite';
import { InstantSearch, SearchBox, Hits, Configure } from 'react-instantsearch-dom';
import 'instantsearch.css/themes/satellite.css';
import { Hit } from './Hit';

const searchClient = algoliasearch("FOEOURC6HS", "881d1efc2a907d9f5b57faf1a347e9c3");

export const Search = () => {
  return (
    <InstantSearch
      searchClient={searchClient}
      indexName="ScrapperPhoneNumberFacebookLinksAddresses"
    >
      <Configure hitsPerPage={5} />
      <div className="ais-InstantSearch">
        <SearchBox />
        <Hits hitComponent={Hit} />
      </div>
    </InstantSearch>
  );
};