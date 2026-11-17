"""Read-only provider audit; preserve quota accounting without creating any posts."""
import json
import os
import buffer_runner as buffer
import tiktok_runner as common


def run():
    state = common.load_json(common.STATE_PATH, {'posts': {}})
    client = buffer.Client(state)
    channel_id = os.environ['BUFFER_CHANNEL_ID']
    channel = client.call(buffer.CHANNEL_QUERY, {'input': {'id': channel_id}})['channel']
    buffer.check_channel(channel, channel_id)
    pending = client.call('''query($input: PostsInput!) { posts(input: $input) {
        edges { node { '''+buffer.POST_FIELDS+''' } } pageInfo { hasNextPage }
    } }''', {'input': {'organizationId': channel['organizationId'],
                      'filter': {'status': ['scheduled', 'sending']}}})['posts']
    # Independently fetch the last known posts, even when local state is complete.
    latest = sorted((e for e in state['posts'].values() if e.get('buffer_post_id')),
                    key=lambda e: str(e.get('scheduled_at', '')))[-4:]
    selections = [f'p{i}: post(input: {{id: {json.dumps(e["buffer_post_id"])}}}) {{ {buffer.POST_FIELDS} }}'
                  for i, e in enumerate(latest)]
    remote = client.call('query { '+' '.join(selections)+' }', {}) if selections else {}
    result = {'channel': channel, 'pending': pending, 'latest_provider_posts': remote,
              'read_only': True, 'publication_attempted': False, 'at': common.iso_now()}
    common.save_json(common.ROOT/'operational_audit.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    run()
